/*
*
* MIT License
*
* Copyright (c) 2025 Luyi Li, Jangseon Park
* Affiliation: University of California San Diego CSE
* Email: lul014@ucsd.edu, jap036@ucsd.edu
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in
* all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
* SOFTWARE.
*
*/

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/string.h>
#include <linux/slab.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <asm/processor.h>
#include <linux/kthread.h>
#include <linux/numa.h>
#include <linux/io.h>
#include <linux/ktime.h>

#define DEVICE_NAME "pointer_chasing"

#define PCH_IOC_MAGIC   'p'
#define PCH_IOC_RUN     _IOWR(PCH_IOC_MAGIC, 1, pchasing_args_t)
#define PCH_IOC_STOP    _IO(PCH_IOC_MAGIC, 2)

#ifndef PCH_BLOCK_SIZE
#define PCH_BLOCK_SIZE  64ULL
#endif

#define RDRAND_MAX_RETRY 32

typedef struct pchasing_args {
  uint64_t in_block_num;
  uint64_t in_stride_size;
  uint64_t in_repeat;
  uint64_t in_core_id; 
  uint64_t in_node_id;
  uint64_t in_use_flush;
  uint64_t in_flush_type;
  uint64_t in_access_order;
  uint64_t in_dimm_start_addr_phys;
  uint64_t in_cxl_start_addr_phys;
  uint64_t in_test_size;
  uint64_t in_snc_mode;
  uint64_t in_socket_num;
  uint64_t in_test_type;
  uint64_t in_ldst_type;
  uint64_t out_latency_cycle_ld;
  uint64_t out_latency_cycle_st;
  uint64_t out_total_cycle_ld;
  uint64_t out_total_cycle_st;
  uint64_t out_total_ns_ld;
  uint64_t out_total_ns_st;
} pchasing_args_t;

static struct task_struct *pch_thread;
static struct completion pch_comp;

static inline __attribute__((always_inline)) uint64_t pch_rdtscp(void)
{
  uint32_t lo, hi;
  asm volatile (
      "rdtscp\n\t"
      "lfence\n\t"
      : "=a" (lo), "=d" (hi)
      :: "%rcx"
  );
  return ((uint64_t)hi << 32) | lo;
}

static inline __attribute__((always_inline)) void pch_serialization(void) {
  uint32_t eax = 0;
  uint32_t ebx, ecx, edx;
  __asm__ __volatile__(
      "cpuid"
      : "=a" (eax), "=b" (ebx), "=c" (ecx), "=d" (edx)
      : "0" (eax)
      : "memory"
  );
}

static inline __attribute__((always_inline)) void pch_mfence(void)
{
  asm volatile("mfence" ::: "memory");
}

static inline __attribute__((always_inline)) void pch_clflush(void *addr)
{
  asm volatile("clflush (%0)" :: "r"(addr));
}

static inline __attribute__((always_inline)) void pch_clflushopt(void *addr)
{
  asm volatile("clflushopt (%0)" :: "r"(addr));
}

static inline __attribute__((always_inline)) void pch_clwb(void *addr)
{
  asm volatile("clwb (%0)" :: "r"(addr));
}

static inline int get_rand(uint64_t *rd, uint64_t range)
{
  uint8_t ok;
  int i = 0;

  for (i = 0; i < RDRAND_MAX_RETRY; i++) {
    asm volatile(
      "rdrand %0\n\t"
      "setc   %1\n\t"
      : "=r"(*rd), "=qm"(ok)
    );

    if (ok) {
      *rd = *rd % range;
      return 0;
    }
  }

  return 1;
}

static int init_chasing_index(uint64_t *cindex, uint64_t csize, uint64_t access_order) {
  uint64_t curr_pos = 0;
  uint64_t next_pos = 0;
  uint64_t i = 0;
  int ret = 0;

    pr_info("%s: csize: %llu\n", __func__, csize);

    if (access_order == 0) {
        for (i = 0; i < csize - 1; i++) {
            do {
                ret = get_rand(&next_pos, csize);
                if (ret != 0)
                    return 1;
            } while ((cindex[next_pos] != 0) || (next_pos == curr_pos));
            cindex[curr_pos] = next_pos;
            curr_pos = next_pos;
        }
        pr_info("%s: generating random cindex...\n", __func__);
    }
    else {
        for (i = 0; i < csize - 1; i++) {
            next_pos = curr_pos + 1;
            cindex[curr_pos] = next_pos;
            curr_pos++;
        }
        pr_info("%s: generating sequential cindex...\n", __func__);
    }
  return 0;
}

static void pointer_chasing_reset(uint64_t *base_addr,
                          uint64_t block_num,
                          uint64_t stride_size,
                          uint64_t *cindex)
{
  uint64_t accessed_block_num = 0;
  uint64_t curr_pos = 0;
  while (accessed_block_num < block_num) {
      uint64_t *curr_addr = (uint64_t *)((uint64_t)base_addr + curr_pos * stride_size);

      *curr_addr = 0;

      curr_pos = cindex[curr_pos];
      accessed_block_num++;
  } 
}

static void pointer_chasing_store(uint64_t *base_addr,
                          uint64_t block_num,
                          uint64_t stride_size,
                          uint64_t repeat,
                          uint64_t *cindex,
                          uint64_t *timing_store,
                          uint64_t use_flush,
                          uint64_t flush_type,
                          uint64_t test_type,
                          uint64_t ldst_type)
{
  int i = 0;

  for (i = 0; i < repeat; i++) {
      uint64_t accessed_block_num = 0;
      uint64_t curr_pos = 0;
      uint64_t next_pos = 0;
      while (accessed_block_num < block_num) {
          uint64_t *curr_addr = (uint64_t *)((uint64_t)base_addr + curr_pos * stride_size);
          next_pos = cindex[curr_pos];

          pch_mfence();
          uint64_t start = pch_rdtscp();

          // store operation
          // *curr_addr = next_pos;
          __asm__ volatile(
              "movq %[val], (%[addr])\n\t"
              :
              : [val] "r" (next_pos), [addr] "r" (curr_addr)
              : "memory"
          );

          pch_mfence();
          uint64_t end = pch_rdtscp();
          timing_store[i] += end - start;
          
          curr_pos = next_pos;
          accessed_block_num++;
      }
      
      if (use_flush) {
          accessed_block_num = 0;
          curr_pos = 0;
          next_pos = 0;
          uint64_t start, end;
          pch_serialization();
          if (test_type == 1) { // flush latency test
              start = pch_rdtscp();
          }
          while (accessed_block_num < block_num) {
              uint64_t *curr_addr = (uint64_t *)((uint64_t)base_addr + curr_pos * stride_size);
              if (flush_type == 0) pch_clflush(curr_addr);
              else if (flush_type == 1) pch_clflushopt(curr_addr);
              else if (flush_type == 2) pch_clwb(curr_addr);
              next_pos = cindex[curr_pos];
              curr_pos = next_pos;
              accessed_block_num++;
          }
          pch_serialization();
          if (test_type == 1) {
              end = pch_rdtscp();
              timing_store[i] = end - start;
          }
      }
  }
}

static void pointer_chasing_load(uint64_t *base_addr,
                          uint64_t block_num,
                          uint64_t stride_size,
                          uint64_t repeat,
                          uint64_t *cindex,
                          uint64_t *timing_load,
                          uint64_t use_flush,
                          uint64_t flush_type,
                          uint64_t test_type,
                          uint64_t ldst_type)
{
  int i = 0;

  for (i = 0; i < repeat; i++) {
      uint64_t accessed_block_num = 0;
      uint64_t curr_pos = 0;
      uint64_t next_pos = 0;
      while (accessed_block_num < block_num) {
          uint64_t *curr_addr = (uint64_t *)((uint64_t)base_addr + curr_pos * stride_size);

          pch_mfence();
          uint64_t start = pch_rdtscp();

          // load operation
          // next_pos = *curr_addr;
          __asm__ volatile(
              "movq (%[addr]), %[val]\n\t"
              : [val] "=r" (next_pos)
              : [addr] "r" (curr_addr)
              : "memory"
          );    

          pch_mfence();
          uint64_t end = pch_rdtscp();
          timing_load[i] += end - start;

          curr_pos = next_pos;
          accessed_block_num++;
      }

      if (use_flush) {
          accessed_block_num = 0;
          curr_pos = 0;
          next_pos = 0;
          uint64_t start, end;
          pch_serialization();
          if (test_type == 1) { // flush latency test
              start = pch_rdtscp();
          }
          while (accessed_block_num < block_num) {
              uint64_t *curr_addr = (uint64_t *)((uint64_t)base_addr + curr_pos * stride_size);
              if (flush_type == 0) pch_clflush(curr_addr);
              else if (flush_type == 1) pch_clflushopt(curr_addr);
              else if (flush_type == 2) pch_clwb(curr_addr);
              next_pos = cindex[curr_pos];
              curr_pos = next_pos;
              accessed_block_num++;
          }
          pch_serialization();
          if (test_type == 1) {
              end = pch_rdtscp();
              timing_load[i] = end - start;
          }
      }
  }
}


static int pointer_chasing_thread(void *data)
{
  pchasing_args_t *args = (pchasing_args_t *)data;
  void *base_addr_virt = NULL;
  uint64_t base_addr_phys = 0;
  uint64_t block_num = args->in_block_num;
  uint64_t stride_size = args->in_stride_size;
  uint64_t repeat = args->in_repeat;
  uint64_t core_id = args->in_core_id;
  uint64_t node_id = args->in_node_id;
  uint64_t use_flush = args->in_use_flush;
  uint64_t access_order = args->in_access_order;
  uint64_t dimm_start_addr_phys = args->in_dimm_start_addr_phys;
  uint64_t cxl_start_addr_phys = args->in_cxl_start_addr_phys;
  uint64_t test_size = args->in_test_size;
  uint64_t snc_mode = args->in_snc_mode;
  uint64_t socket_num = args->in_socket_num;
  uint64_t ldst_type = args->in_ldst_type;
  uint64_t test_type = args->in_test_type;
  uint64_t flush_type = args->in_flush_type;
  uint64_t cxl_mem_node = snc_mode * socket_num;
  uint64_t region_skip = block_num * stride_size;
  uint64_t *cindex = NULL;
  uint64_t *timing_ld  = NULL;
  uint64_t *timing_st = NULL;
  int online_numa_node_count = num_online_nodes();
  uint64_t node_start_t, node_end_t;
  int i;
  uint64_t hash = 0;
  uint64_t *buf;
  int pages;
  uint64_t *test_buf;
  uint64_t start_cycle_st, end_cycle_st, start_cycle_ld, end_cycle_ld;
  uint64_t start_ns_st, end_ns_st, start_ns_ld, end_ns_ld;
  uint64_t sum_st = 0, sum_ld = 0;

  pr_info("%s: number of online NUMA nodes: %d\n", __func__, online_numa_node_count);

  for (i = 0; i < online_numa_node_count; i++) {
    node_start_t = node_start_pfn(i) << PAGE_SHIFT;
    node_end_t   = node_end_pfn(i) << PAGE_SHIFT;
    pr_info("%s: NUMA node [%d] start [0x%llx] end [0x%llx]\n", 
        __func__, i, node_start_t, node_end_t);
  }

  if (!node_online(node_id)) {
    pr_err("Node %llu is not online or does not exist.\n", node_id);
    complete(&pch_comp);
    return -ENODEV;
  }

  pr_info("%s: started pointer-chasing on CPU [%llu] and NUMA node [%llu]\n", __func__, core_id, node_id);

  if (node_id == 0) {
      base_addr_phys = dimm_start_addr_phys;
      base_addr_virt = phys_to_virt(base_addr_phys);
  }
  else if (node_id == cxl_mem_node) {
      base_addr_phys = cxl_start_addr_phys + (1ULL<<30ULL);
      base_addr_virt = phys_to_virt(base_addr_phys);
  }
  else {
      pr_err("pointer-chasing is not supported on this node.\n");
      complete(&pch_comp);
      return -EINVAL;
  }
  
  pr_info("%s: phys_addr: 0x%llx, virt_addr: 0x%llx, size: 0x%llx\n", __func__, base_addr_phys, (uint64_t)base_addr_virt, test_size);

  /* fill page tables */
  pages = roundup(2 * region_skip, PAGE_SIZE) >> PAGE_SHIFT;
  for (i = 0; i < pages; i++) {
    buf  = (uint64_t *)base_addr_virt + (i << PAGE_SHIFT);
    hash = hash ^ *buf;
  }

  cindex = (uint64_t*)base_addr_virt; //(uint64_t*)kmalloc(sizeof(uint64_t)*block_num, GFP_KERNEL);
  timing_st = (uint64_t*)kmalloc(sizeof(uint64_t)*repeat, GFP_KERNEL);
  timing_ld = (uint64_t*)kmalloc(sizeof(uint64_t)*repeat, GFP_KERNEL);

  if (!timing_ld || !timing_st) {
      pr_err("kmalloc failed.\n");
      kfree(timing_st);
      kfree(timing_ld);
      complete(&pch_comp);
      return -ENOMEM;
  }

  memset(cindex, 0, sizeof(uint64_t)*block_num);
  memset(timing_st, 0, sizeof(uint64_t)*repeat);
  memset(timing_ld, 0, sizeof(uint64_t)*repeat);

  if (init_chasing_index(cindex, block_num, access_order) != 0) {
      pr_err("init_chasing_index failed.\n");
      memset(cindex, 0, sizeof(uint64_t)*block_num);
      kfree(timing_st);
      kfree(timing_ld);
      complete(&pch_comp);
      return -EFAULT;
  }
  pr_info("%s: finished cindex generation.\n", __func__);

  test_buf = (uint64_t *)((uint64_t)base_addr_virt + 0x40000000); // First 1GB for storing cindex

  pch_mfence();
  start_cycle_st = pch_rdtscp();
  start_ns_st = ktime_get_ns();
  pointer_chasing_store(test_buf, block_num, stride_size, repeat, cindex, timing_st, use_flush, flush_type, test_type, ldst_type);
  pch_mfence();
  end_cycle_st = pch_rdtscp();
  end_ns_st = ktime_get_ns();
  pr_info("%s: finished store pointer-chasing, start_cycle: %llu, end_cycle: %llu, start_ns: %llu, end_ns: %llu\n"
          , __func__, start_cycle_st, end_cycle_st, start_ns_st, end_ns_st);
  
  pch_mfence();
  start_cycle_ld = pch_rdtscp();
  start_ns_ld = ktime_get_ns();
  pointer_chasing_load(test_buf, block_num, stride_size, repeat, cindex, timing_ld, use_flush, flush_type, test_type, ldst_type);
  pch_mfence();
  end_cycle_ld = pch_rdtscp();
  end_ns_ld = ktime_get_ns();
  pr_info("%s: finished load pointer-chasing, start_cycle: %llu, end_cycle: %llu, start_ns: %llu, end_ns: %llu\n"
          , __func__, start_cycle_ld, end_cycle_ld, start_ns_ld, end_ns_ld);

  for (i = 1; i < repeat; i++) {
      sum_st += timing_st[i];
      sum_ld += timing_ld[i];
  }
  args->out_latency_cycle_st = sum_st / block_num / (repeat - 1);
  args->out_latency_cycle_ld = sum_ld / block_num / (repeat - 1);
  args->out_total_cycle_st = end_cycle_st - start_cycle_st;
  args->out_total_cycle_ld = end_cycle_ld - start_cycle_ld;
  args->out_total_ns_st = end_ns_st - start_ns_st;
  args->out_total_ns_ld = end_ns_ld - start_ns_ld;

  pointer_chasing_reset((uint64_t *)base_addr_virt, block_num, stride_size, cindex);
  // pr_info("%s: finished reset pointer-chasing.\n", __func__);

  memset(cindex, 0, sizeof(uint64_t)*block_num);
  kfree(timing_st);
  kfree(timing_ld);
  complete(&pch_comp);
  pr_info("%s: finished pointer-chasing\n", __func__);
  return 0;
}

static long pointer_chasing_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
  pchasing_args_t karg;
  int ret;

  if (_IOC_TYPE(cmd) != PCH_IOC_MAGIC) {
      pr_err("Invalid magic number.\n");
      return -EINVAL;
  }

  switch (cmd) {
  case PCH_IOC_RUN:
      if (copy_from_user(&karg, (void __user *)arg, sizeof(karg))) {
          pr_err("copy_from_user failed.\n");
          return -EFAULT;
      }

      pr_info("%s: block_num=%llu, stride_size=%llu, repeat=%llu, core_id=%llu, node_id=%llu, flush=%llu\n, access_order=%llu\n", 
              __func__,
              karg.in_block_num,
              karg.in_stride_size,
              karg.in_repeat,
              karg.in_core_id,
              karg.in_node_id,
              karg.in_use_flush,
              karg.in_access_order);

      if (pch_thread) {
          pr_info("%s: Thread already exists, please stop it first or handle accordingly.\n", __func__);
          kthread_stop(pch_thread);
          pch_thread = NULL;
      }

      init_completion(&pch_comp);

      pch_thread = kthread_create(pointer_chasing_thread, (void *)&karg, "pch_thread");
      if (IS_ERR(pch_thread)) {
          pr_err("kthread_create failed.\n");
          pch_thread = NULL;
          return PTR_ERR(pch_thread);
      }

      kthread_bind(pch_thread, (int)karg.in_core_id);
      wake_up_process(pch_thread);
      // wait_for_completion(&pch_comp);
      ret = wait_for_completion_interruptible(&pch_comp);
      kthread_stop(pch_thread);
      pch_thread = NULL;
      pr_info("%s: pointer_chasing_thread finished.\n", __func__);

      if (copy_to_user((void __user *)arg, &karg, sizeof(karg))) {
          pr_err("copy_to_user failed.\n");
          return -EFAULT;
      }

      break;

  case PCH_IOC_STOP:
      if (pch_thread) {
          pr_info("%s: stopping thread.\n", __func__);
          kthread_stop(pch_thread);
          pch_thread = NULL;
      } else {
          pr_info("%s: no thread running.\n", __func__);
      }
      break;

  default:
      pr_err("Unknown cmd.\n");
      return -EINVAL;
  }

  return 0;
}

static struct file_operations pointer_chasing_fops = {
    .owner          = THIS_MODULE,
    .unlocked_ioctl = pointer_chasing_ioctl,
};

static dev_t pch_dev;
static struct cdev pch_cdev;
static struct class *pch_class;

static int __init pointer_chasing_init(void)
{
  int ret;

  pr_info("%s: pointer_chasing module loaded.\n", __func__);

  ret = alloc_chrdev_region(&pch_dev, 0, 1, DEVICE_NAME);
  if (ret < 0) {
      pr_err("alloc_chrdev_region failed.\n");
      return ret;
  }

  cdev_init(&pch_cdev, &pointer_chasing_fops);
  pch_cdev.owner = THIS_MODULE;

  ret = cdev_add(&pch_cdev, pch_dev, 1);
  if (ret < 0) {
      pr_err("cdev_add failed.\n");
      unregister_chrdev_region(pch_dev, 1);
      return ret;
  }

  pch_class = class_create(DEVICE_NAME);
  if (IS_ERR(pch_class)) {
      pr_err("class_create failed.\n");
      cdev_del(&pch_cdev);
      unregister_chrdev_region(pch_dev, 1);
      return PTR_ERR(pch_class);
  }

  device_create(pch_class, NULL, pch_dev, NULL, DEVICE_NAME);

  return 0;
}

static void __exit pointer_chasing_exit(void)
{
  if (pch_thread) {
      pr_info("%s: stopping pointer-chasing thread...\n", __func__);
      kthread_stop(pch_thread);
      pch_thread = NULL;
  }

  device_destroy(pch_class, pch_dev);
  class_destroy(pch_class);

  cdev_del(&pch_cdev);
  unregister_chrdev_region(pch_dev, 1);

  pr_info("%s: pointer_chasing module unloaded.\n", __func__);
}

module_init(pointer_chasing_init);
module_exit(pointer_chasing_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("CXL_Perf");
MODULE_DESCRIPTION("Pointer Chasing Module");

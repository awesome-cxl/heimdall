#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/numa.h>

static int __init numa_info_init(void)
{
    int i, online_numa_node_count;
    unsigned long long node_start_t, node_end_t;

    online_numa_node_count = num_online_nodes();
    pr_info("%s: Total online NUMA nodes: %d\n", __func__, online_numa_node_count);

    for (i = 0; i < online_numa_node_count; i++) {
        node_start_t = (unsigned long long)node_start_pfn(i) << PAGE_SHIFT;
        node_end_t = (unsigned long long)node_end_pfn(i) << PAGE_SHIFT;
        pr_info("%s: NUMA node [%d] start [0x%llx] end [0x%llx]\n",
                __func__, i, node_start_t, node_end_t);
    }

    return 0;
}

static void __exit numa_info_exit(void)
{
    pr_info("%s: Module unloaded\n", __func__);
}

module_init(numa_info_init);
module_exit(numa_info_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("CXL_Perf");
MODULE_DESCRIPTION("Print NUMA node physical address ranges");
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

#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <utils/input_parser.h>
#include <utils/logger.h>
#include <signal.h>

#define PCH_IOC_MAGIC 'p'
#define PCH_IOC_RUN     _IOWR(PCH_IOC_MAGIC, 1, pchasing_args_t)
#define PCH_IOC_STOP    _IO(PCH_IOC_MAGIC, 2)

static int fd = -1;

void signal_handler(int sig) {
  if (sig == SIGINT) {
      printf("Caught Ctrl+C, stopping thread...\n");
      if (fd >= 0) {
          if (ioctl(fd, PCH_IOC_STOP) < 0) {
              perror("ioctl PCH_IOC_STOP failed");
          }
          close(fd);
      }
      exit(0);
  }
}

int prepare(pchasing_args_t &args, int argc, char *argv[]) {
  InputParserForCache parser;
  std::tuple<std::string, std::string> files = parser.parse(argc, argv);
  parser.parse(std::get<0>(files), &args);
  Logger::get_instance().open(std::get<1>(files));
  int fd = open("/dev/pointer_chasing", O_RDWR);
  if (fd < 0) {
    perror("open");
    return -1;
  }

  std::string access_order = (args.in_access_order == 0) ? "random" : "sequential";
  std::string test_type = (args.in_test_type == 0) ? "access latency" : "flush latency";
  std::string flush_type = "unkown";
  std::string ldst_type = "unkown";
  if (args.in_flush_type == 0) {
    flush_type = "clflush";
  } else if (args.in_flush_type == 1) {
    flush_type = "clflushopt";
  } else if (args.in_flush_type == 2) {
    flush_type = "clwb";
  }
  
  if (args.in_ldst_type == 0) {
    ldst_type = "temporal";
  } else if (args.in_ldst_type == 1) {
    ldst_type = "non-temporal";
  } else if (args.in_ldst_type == 2) {
    ldst_type = "atomic";
  }

  std::stringstream dimm_addr_hex, cxl_addr_hex;
  dimm_addr_hex << "0x" << std::hex << args.in_dimm_start_addr_phys;
  cxl_addr_hex << "0x" << std::hex << args.in_cxl_start_addr_phys;

  std::string test_info =
      "=============== Test Information ===============\n"
      "Test Type: " + test_type + "\n" +
      "Number of Block: " +
      std::to_string(args.in_block_num) + "\n" +
      "Stride Size: " + std::to_string(args.in_stride_size) + "\n" +
      "DIMM Start Physical Address: " + dimm_addr_hex.str() + "\n" +
      "CXL Start Physical Address: " + cxl_addr_hex.str() + "\n" +
      "Test Size: " + std::to_string(args.in_test_size) + "\n" +
      "SNC Mode: " + std::to_string(args.in_snc_mode) + "\n" +
      "Socket Number: " + std::to_string(args.in_socket_num) + "\n" +
      "Test Size: " + std::to_string(args.in_test_size) + "\n" +
      "Repeat: " + std::to_string(args.in_repeat) + "\n" +
      "Core ID: " + std::to_string(args.in_core_id) + "\n" +
      "Node ID: " + std::to_string(args.in_node_id) + "\n" +
      "Use Flush: " + std::to_string(args.in_use_flush) + "\n" +
      "Flush Type: " + flush_type + "\n" +
      "Access Order: " + access_order + "\n" +
      "Load/Store Type: " + ldst_type + "\n" + "\n";
  Logger::get_instance().append(test_info);
  return fd;
}

void wrap_up(int fd, pchasing_args_t &args) {
  double ns_per_cycle_st =
      (double)args.out_total_ns_st / args.out_total_cycle_st;
  double ns_per_cycle_ld =
      (double)args.out_total_ns_ld / args.out_total_cycle_ld;
  double out_latency_ns_st =
      (double)args.out_latency_cycle_st * ns_per_cycle_st;
  double out_latency_ns_ld =
      (double)args.out_latency_cycle_ld * ns_per_cycle_ld;

  std::string log = " ";
  if (args.in_test_type == 0) {
    log =
        "=============== Test Results ===============\n"
        "Average Store Latency: " + std::to_string(args.out_latency_cycle_st) +
        " cycles, " + std::to_string(out_latency_ns_st) + " ns\n" +
        "Average Load Latency: " + std::to_string(args.out_latency_cycle_ld) +
        " cycles, " + std::to_string(out_latency_ns_ld) + " ns\n" + "\n";
  }
  else if (args.in_test_type == 1) {
    log =
        "=============== Test Results ===============\n"
        "Average Dirty Flush Latency: " + std::to_string(args.out_latency_cycle_st) +
        " cycles, " + std::to_string(out_latency_ns_st) + " ns\n" +
        "Average Clean Flush Latency: " + std::to_string(args.out_latency_cycle_ld) +
        " cycles, " + std::to_string(out_latency_ns_ld) + " ns\n" + "\n";
  }
  
  Logger::get_instance().append(log);
  Logger::get_instance().close();
  close(fd);
}

int main(int argc, char *argv[]) {
  signal(SIGINT, signal_handler);

  pchasing_args_t args;
  memset(&args, 0, sizeof(args));
  fd = prepare(args, argc, argv);

  uint64_t region_skip = args.in_block_num * args.in_stride_size;
  if (region_skip >= args.in_test_size) {
    return -1;
  }

  int ret = ioctl(fd, PCH_IOC_RUN, &args);
  if (ret < 0) {
    perror("ioctl PCH_IOC_RUN");
    close(fd);
    return 1;
  }
  wrap_up(fd, args);

  return 0;
}

/*
 *
 * MIT License
 *
 * Copyright (c) 2025 Jangseon Park
 * Affiliation: University of California San Diego CSE
 * Email: jap036@ucsd.edu
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

#include <iostream>
#include <utils/input_parser.h>
#include <yaml-cpp/yaml.h>

std::tuple<std::string, std::string> InputParserForBW::parse(int argc,
                                                             char *argv[]) {
  if (argc < 4) {
    std::cerr << "Usage: " << argv[0] << " -f <script_path> -o <output_path>\n";
  }
  std::string script_path;
  std::string output_path;

  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "-f" && i + 1 < argc) {
      script_path = argv[++i];
    } else if (arg == "-o" && i + 1 < argc) {
      output_path = argv[++i];
    } else {
      std::cerr << "Unknown or incomplete argument: " << arg << "\n";
    }
  }

  return std::tuple<std::string, std::string>(script_path, output_path);
}

std::shared_ptr<JobInfo> InputParserForBW::parse(const fs::path &input_file) {
  YAML::Node yaml_file = YAML::LoadFile(input_file.string());
  std::shared_ptr<JobInfo> job_info = std::make_shared<JobInfo>();
  std::cout << "Parsing the input file: " << input_file << "\n";
  job_info->job_id = static_cast<JobId>(yaml_file["job_id"].as<uint32_t>());
  job_info->num_threads = yaml_file["num_threads"].as<uint32_t>();
  job_info->lt_pattern_block_size =
      yaml_file["lt_pattern_block_size"].as<uint64_t>();
  job_info->lt_pattern_access_size =
      yaml_file["lt_pattern_access_size"].as<uint64_t>();
  job_info->lt_pattern_stride_size =
      yaml_file["lt_pattern_stride_size"].as<uint64_t>();
  job_info->numa_id =
      static_cast<NumaId>(yaml_file["numa_type"].as<uint32_t>());
  job_info->socket_id =
      static_cast<SocketId>(yaml_file["socket_type"].as<uint32_t>());
  job_info->delay = yaml_file["delay"].as<uint64_t>();
  job_info->ldst_type =
      static_cast<LoadStoreType>(yaml_file["loadstore_type"].as<uint32_t>());
  job_info->mem_alloc_type =
      static_cast<MemAllocType>(yaml_file["mem_alloc_type"].as<uint32_t>());
  job_info->latency_pattern =
      static_cast<LatencyPattern>(yaml_file["latency_pattern"].as<uint32_t>());
  job_info->bw_pattern =
      static_cast<BwPattern>(yaml_file["bandwidth_pattern"].as<uint32_t>());
  job_info->bw_load_pattern_block_size = static_cast<BwPatternSize>(
      yaml_file["bw_load_pattern_block_size"].as<uint32_t>());
  job_info->bw_store_pattern_block_size = static_cast<BwPatternSize>(
      yaml_file["bw_store_pattern_block_size"].as<uint32_t>());
  job_info->pattern_iteration = yaml_file["pattern_iteration"].as<uint32_t>();
  job_info->thread_buffer_size =
      yaml_file["thread_buffer_size"].as<uint64_t>() * MEMUNIT::MiB;
  std::cout << "Job ID: " << static_cast<uint32_t>(job_info->job_id) << "\n";
  return job_info;
}

std::tuple<std::string, std::string> InputParserForCache::parse(int argc,
                                                                char *argv[]) {
  if (argc < 4) {
    std::cerr << "Usage: " << argv[0] << " -f <script_path> -o <output_path>\n";
  }
  std::string script_path;
  std::string output_path;

  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "-f" && i + 1 < argc) {
      script_path = argv[++i];
    } else if (arg == "-o" && i + 1 < argc) {
      output_path = argv[++i];
    } else {
      std::cerr << "Unknown or incomplete argument: " << arg << "\n";
    }
  }

  return std::tuple<std::string, std::string>(script_path, output_path);
}

void InputParserForCache::parse(const fs::path &input_file,
                                pchasing_args_t *args) {
  YAML::Node yaml_file = YAML::LoadFile(input_file.string());
  std::cout << "Parsing the input file: " << input_file << "\n";
  args->in_repeat = yaml_file["repeat"].as<uint64_t>();
  args->in_core_id = yaml_file["core_id"].as<uint64_t>();
  args->in_node_id = yaml_file["node_id"].as<uint64_t>();
  args->in_use_flush = yaml_file["use_flush"].as<uint64_t>();
  args->in_access_order = yaml_file["access_order"].as<uint64_t>();
  args->in_dimm_start_addr_phys =
      yaml_file["dimm_start_addr_phys"].as<uint64_t>();
  args->in_dimm_test_size = yaml_file["dimm_test_size"].as<uint64_t>();
  args->in_stride_size = yaml_file["stride_size"].as<uint64_t>();
  args->in_block_num = yaml_file["block_num"].as<uint64_t>();
  args->in_test_size = yaml_file["test_size"].as<uint64_t>();
  std::cout << "Input file parsed successfully\n";
}

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

#include <core/job_manager.h>
#include <iostream>
#include <utils/logger.h>

JobManager::JobManager() : _worker_factory(std::make_shared<WorkerFactory>()) {}

void JobManager::prepare(const fs::path &output_path,
                         const std::shared_ptr<JobInfo> &jobInfo) {
  Logger::get_instance().open(output_path);
  _worker_handler = _worker_factory->get(jobInfo->job_id);
  if (!_worker_handler) {
    throw std::runtime_error("Worker not found");
  }
  _worker_handler->initialize(jobInfo, Logger::get_instance());
}

void JobManager::run(const fs::path &output_path,
                     const std::shared_ptr<JobInfo> &jobInfo) {
  std::cout << "JobManager::run()" << std::endl;
  prepare(output_path, jobInfo);
  _worker_handler->start();
  _worker_handler->wait();
  wrap_up();
}

void JobManager::wrap_up() {
  _worker_handler->wrap_up();
  _worker_handler->report(Logger::get_instance());
  Logger::get_instance().close();
}

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

#include <core/worker_factory.h>

WorkerFactory::WorkerFactory() {
  _handlers[JobId::BANDWIDTH_LATENCY] =
      std::make_shared<WorkerHandlerForBwVsLatency>();
  _handlers[JobId::BANDWIDTH] = std::make_shared<WorkerHandlerForBandwidth>();
  _handlers[JobId::LATENCY] = std::make_shared<WorkerHandlerForLatency>();
}

WorkerFactory::~WorkerFactory() {}

std::shared_ptr<WorkerHandler> WorkerFactory::get(JobId id) {
  auto it = _handlers.find(id);
  if (it == _handlers.end()) {
    std::cerr << "WorkerFactory::get: No handler for job id "
              << static_cast<uint32_t>(id) << std::endl;
    return nullptr;
  }
  return it->second;
}

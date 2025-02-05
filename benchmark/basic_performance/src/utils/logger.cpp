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
#include <utils/logger.h>

Logger &Logger::get_instance() {
  static Logger logger;
  return logger;
}

void Logger::open(const fs::path &file_path) {
  _file_path = file_path / Timer::get_current_time();
  if (!fs::exists(_file_path)) {
    fs::create_directories(_file_path);
  }
  _file_path += "/result.log";
  std::cout << "Log file path: " << _file_path << std::endl;
  _file.open(_file_path, std::ios::out);
  _timer.start();
}

void Logger::append(const std::string &message) {
  std::string msg =
      "[" + std::to_string(_timer.elapsed()) + "]" + message + "\n";
  std::cout << msg;
  _file << msg;
}

void Logger::close() {
  if (_file.is_open())
    _file.close();
}

Logger::~Logger() { close(); }

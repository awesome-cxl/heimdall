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

#ifndef CXL_PERF_APP_MACHINE_DEFINE_H
#define CXL_PERF_APP_MACHINE_DEFINE_H
#define MACHINE_X86 1
#define MACHINE_ARM 2
#define MACHINE_MOCKUP 3

#ifndef MACHINE_TYPE_DEF
#define MACHINE_TYPE_DEF MACHINE_MOCKUP
#endif

#ifndef CORE_NUM_PER_SOCKET_DEF
#define CORE_NUM_PER_SOCKET_DEF 10
#endif
#endif // CXL_PERF_APP_MACHINE_DEFINE_H

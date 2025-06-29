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

#ifndef CXL_PERF_APP_DT_MACHINE_DEPENDENCY_H
#define CXL_PERF_APP_DT_MACHINE_DEPENDENCY_H
#include <core/machine_define.h>

#if MACHINE_TYPE_DEF == MACHINE_X86
#include <machine/x86/ld_st/ldst_pattern_x86.h>
#include <machine/x86/ld_st/mem_utils_x86.h>
#elif MACHINE_TYPE_DEF == MACHINE_ARM
#include <machine/arm/ldst_pattern_arm.h>
#include <machine/arm/mem_utils_arm.h>
#elif MACHINE_TYPE_DEF == MACHINE_MOCKUP
#include <machine/mockup/ldst_pattern_mockup.h>
#include <machine/mockup/mem_utils_mockup.h>
#endif // MACHINE_TYPE

#endif // CXL_PERF_APP_DT_MACHINE_DEPENDENCY_H

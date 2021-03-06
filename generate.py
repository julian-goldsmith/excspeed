#!/usr/bin/env python3
#
# Copyright (C) 2016 Jussi Pakkanen.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of version 3, or (at your option) any later version,
# of the GNU General Public License as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, shutil

class GenerateCode:

    def __init__(self, max_func, num_rounds, error_perc):
        self.error_perc = error_perc
        self.max_func = max_func
        self.num_rounds = num_rounds
        self.init_cpp()
        self.init_c()

    def init_cpp(self):
        self.cppdir = 'cpp'
        self.cpp_main = '''#include<cstdio>
#include<cstdlib>
#include<funcs.h>

int main(int argc, char **argv) {
    int ok = 0;
    int fail = 0;
    srandom(42); // Must be deterministic and the same for C and C++
    const int rounds = %d;
    for(int i=0; i<rounds; i++) {
        try {
            ok += func0();
        } catch(...) {
            fail++;
        }
    }
    printf("OK: %%d\\nFail: %%d\\n", ok, fail);
    return 0;
}
''' % self.num_rounds
        self.cpp_header_templ = 'int func%d();\n'
        self.cpp_templ = '''#include<cstdlib>
#include<funcs.h>

int func%d() {
    int num = random() %% 5;
    if(num == 0) {
        return func%d();
    }
    if(num == 1) {
        return func%d();
    }
    if(num == 2) {
        return func%d();
    }
    if(num == 3) {
        return func%d();
    }
    return func%d();
}
'''
        self.cpp_last_tmpl = '''#include<stdexcept>
#include<cstdlib>
#include<funcs.h>

int func%d() {
    int x = random() %% 100;
    if(x<%d) {
        throw 1;
    }
    return 1;
}
'''
        self.cpp_mainfile = os.path.join(self.cppdir, 'main.cpp')
        self.cpp_file_templ = os.path.join(self.cppdir, 'func%d.cpp')
        self.cpp_h = os.path.join(self.cppdir, 'funcs.h')
        self.cpp_meson = os.path.join(self.cppdir, 'meson.build')

    def init_c(self):
        self.cdir = 'plainc'
        self.c_main = '''#include<stdio.h>
#include<stdlib.h>
#include<funcs.h>
#include<string.h>

int main(int argc, char **argv) {
    int ok = 0;
    int fail = 0;
    int error = 0;
    srandom(42); // Must be deterministic and the same for C and C++
    const int rounds = %d;
    for(int i=0; i<rounds; i++) {
        int res = func0(&error);

        if(error) {
            fail++;
        } else {
            ok += res;
        }
    }
    printf("OK: %%d\\nFail: %%d\\n", ok, fail);
    return 0;
}
''' % self.num_rounds
        self.c_header_templ = 'int func%d(int *error);\n'
        self.c_templ = '''#include<stdlib.h>
#include<funcs.h>

int func%d(int *error) {
    int num = random() %% 5;

    if(num == 0) {
        return func%d(error);
    }

    if(num == 1) {
        return func%d(error);
    }

    if(num == 2) {
        return func%d(error);
    }

    if(num == 3) {
        return func%d(error);
    }

    return func%d(error);
}
'''
        self.c_last_tmpl = '''#include<string.h>
#include<stdlib.h>
#include<funcs.h>

int func%d(int *error) {
    int x = random() %% 100;

    if(x<%d) {
        *error = 1;     // could be any value
        return -1;
    }

    *error = 0;
    return 1;
}
'''

        self.c_mainfile = os.path.join(self.cdir, 'main.c')
        self.c_file_templ = os.path.join(self.cdir, 'func%d.c')
        self.c_h = os.path.join(self.cdir, 'funcs.h')
        self.c_meson = os.path.join(self.cdir, 'meson.build')

    def deltrees(self):
        if os.path.exists(self.cppdir):
            shutil.rmtree(self.cppdir)
        os.mkdir(self.cppdir)
        if os.path.exists(self.cdir):
            shutil.rmtree(self.cdir)
        os.mkdir(self.cdir)

    def run(self):
        self.deltrees()
        self.generate_cpp()
        self.generate_c()

    def generate_cpp(self):
        open(self.cpp_mainfile, 'w').write(self.cpp_main)
        for i in range(self.max_func):
            code = self.cpp_templ % (i,
                                     min(i+1, self.max_func),
                                     min(i+2, self.max_func),
                                     min(i+3, self.max_func),
                                     min(i+4, self.max_func),
                                     min(i+5, self.max_func),
                                     )
            fname = self.cpp_file_templ % i
            open(fname, 'w').write(code)
        bottom_code = self.cpp_last_tmpl % (self.max_func, self.error_perc)
        fname = self.cpp_file_templ % self.max_func
        open(fname, 'w').write(bottom_code)
        with open(self.cpp_h, 'w') as ofile:
            ofile.write('#pragma once\n')
            for i in range(self.max_func+1):
                ofile.write('int func%d();\n' % i)
        with open(self.cpp_meson, 'w') as ofile:
            ofile.write('''project('exceptionspeed', 'cpp',
    default_options : ['buildtype=debugoptimized', 'cpp_std=c++14'])

executable('cppprog', 'main.cpp',
''')
            for i in range(self.max_func+1):
                ofile.write(" 'func%d.cpp',\n" % i)
            ofile.write(')\n')

    def generate_c(self):
        open(self.c_mainfile, 'w').write(self.c_main)
        for i in range(self.max_func):
            code = self.c_templ % (i,
                                   min(i+1, self.max_func),
                                   min(i+2, self.max_func),
                                   min(i+3, self.max_func),
                                   min(i+4, self.max_func),
                                   min(i+5, self.max_func),
                                   )
            fname = self.c_file_templ % i
            open(fname, 'w').write(code)
        bottom_code = self.c_last_tmpl % (self.max_func, self.error_perc)
        fname = self.c_file_templ % self.max_func
        open(fname, 'w').write(bottom_code)
        with open(self.c_h, 'w') as ofile:
            ofile.write('#pragma once\n')
            ofile.write('''''')
            for i in range(self.max_func+1):
                ofile.write('int func%d(int *error);\n' % i)
        with open(self.c_meson, 'w') as ofile:
            ofile.write('''project('exceptionspeed', 'c',
    default_options : ['buildtype=debugoptimized', 'c_std=gnu99'])

executable('cprog', 'main.c',
''')
            for i in range(self.max_func+1):
                ofile.write(" 'func%d.c',\n" % i)
            ofile.write(')\n')

if __name__ == '__main__':
    g = GenerateCode(100, 10000, 1)
    g.run()

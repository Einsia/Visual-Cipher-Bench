#!/bin/sh
# Build on a Linux x86-64 machine with a C++17 compiler and static C++/C libraries.
# The offline runtime does not need a compiler, shared C++ runtime, or SAT package.
set -eu
cd "$(dirname "$0")"
"${CXX:-g++}" -O3 -std=c++17 -static engine.cpp -o engine.next
mv engine.next engine

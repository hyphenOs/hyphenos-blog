Title: On Ftrace, kprobes, tracepoints
Date: 2017-08-09
Tags: linux-kernel, tracing, bpf, ftrace
Category: Performance
Slug: on-ftrace-kprobes-tracepoints.md
Author: Abhijit Gadgil
Summary: For a beginner, tracing infrastructure in Linux can be considerably confusing. It's easier to get lost while trying to figure out what exactly are tracing mechanisms, which ones should be used. Addition of new eBPF support for tracing has added more to it. This is just an attempt to compile what is my current understanding, with a slightly more bias towards what facilities eBPF provides, as this is the state of the art.

Note: This is going to start more as a brain-dump and over a period of time, I am going to iterate over this, till it comes in some consumable form.

Most of the Linux dynamic tracing is built around the core support in kernel called `Ftrace`, this started as a function trace sub-system, but is considerably more involved now. All the major tools like [LTTng](https://lttng.org/), [SystemTap](https://sourceware.org/systemtap/) or the more recent [BCC](https://github.com/iovisor/bcc) make use of this infrastructure and then build upon it. In fact some of the kernel developments like `kprobes` and `uprobes` were developed in SystemTap project.

Found a [good presentation](http://events.linuxfoundation.org/images/stories/pdf/lceu2012_zannoni.pdf), that provides a historical perspective of how many of these projects are started. I have also created a [clipboard](https://www.slideshare.net/gabhijit1/clipboards/linux-tracing), that give a timeline of Linux tracing and evolution of BPF support. This helped me understand why some of the utilities in `bcc` won't run on my Ubuntu 16.04 system.

Arguably one of the best (if not the best) resource about Linux tracing is [Brendan Gregg's Blog](http://www.brendangregg.com/).

Coming back to specifics - it is possible to 'trace' following -

1. A vast majority of kernel functions - those available inside `/sys/kernel/debug/tracing/available_filter_functions`. (This assumes you have mounted the `tracefs` in more recent kernels (and `debugfs` in slightly older kernels) on the `/sys/kernel/debug/tracing` path. It's possible to trace only a subset of those functions or functions belonging to a particular subsystem like say `net` etc. Kernel's documentation is a good starting point inside `Documentation/trace/ftrace.txt' and a few other files.

2. `kprobes` provided a mechanism to trace both `entry` and `exit` of a function. However the mechanism to do this was slightly involved, in the absence of integration with `ftrace` mechanism (basically a similar mechanism to trace functions above). However with `ftrace` support for `kprobes`, this has become very useful.

3. In addition there are a number of `tracepoints` defined in various subsystems. But it's not quite clear to me - which are the use cases where it would make sense to use this mechanims as opposed to one of the above, which seem to be very flexible.

4. `perf` events (not fully understood yet).

5. Userspace probing (not fully understood it yet).

The recent eBPF has made tracing a lot more interesting. What eBPF essentially allows is adding a code from Userspace to the kernel at the runtime, that can be interfaced with the above `ftrace` mechanism. `bcc` pointed above, has developed a lot of useful tools using this mechanism.

I will keep updating this article as we go along.

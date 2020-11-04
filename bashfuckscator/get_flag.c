#include <unistd.h>

int main() {
        setuid(0);
        seteuid(0);
        char* argv[] = {"/bin/bash", "/get_flag.sh", NULL};
        execv("/bin/bash", argv);
}

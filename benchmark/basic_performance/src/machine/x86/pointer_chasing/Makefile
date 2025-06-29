obj-m += pointer_chasing.o
KDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)
OUTPUT_DIR := $(PWD)/../../../../build/cache_test/module/build/kernel
$(shell mkdir -p $(OUTPUT_DIR))

all:
	$(MAKE) -C $(KDIR) M=$(PWD) O=$(OUTPUT_DIR) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) O=$(OUTPUT_DIR) clean

install:
	sudo insmod $(OUTPUT_DIR)/pointer_chasing.ko

uninstall:
	sudo rmmod pointer_chasing

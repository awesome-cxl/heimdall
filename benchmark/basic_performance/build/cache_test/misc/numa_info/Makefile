obj-m += numa_info.o

all:
	@echo "Building kernel module..."
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
	@echo "Checking if numa_info module is loaded..."
	@if lsmod | grep -q numa_info; then \
		echo "Unloading existing numa_info module..."; \
		sudo rmmod numa_info; \
	fi
	@echo "Loading numa_info module..."
	sudo insmod numa_info.ko
	@echo "Checking kernel logs for numa_info_init..."
	sudo dmesg | grep numa_info_init

clean:
	@echo "Cleaning up..."
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
	@echo "Checking if numa_info module is loaded..."
	@if lsmod | grep -q numa_info; then \
		echo "Unloading numa_info module..."; \
		sudo rmmod numa_info; \
	fi
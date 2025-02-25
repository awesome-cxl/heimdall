SANITIZE_FLAGS := -fsanitize=undefined,address

LIB_DIR = $(realpath ./libs)

FOLLY_PKG_CONFIG_PATH = $(LIB_DIR)/folly/folly/lib/pkgconfig
FMT_LIB_PATH = $(shell ls "$(LIB_DIR)"/folly/ | grep fmt)
FMT_PKG_CONFIG_PATH = $(LIB_DIR)/folly/$(FMT_LIB_PATH)/lib/pkgconfig
PKG_CONFIG_PATH = $(FMT_PKG_CONFIG_PATH):$(FOLLY_PKG_CONFIG_PATH)

# Extract directories of shared libraries from pkg-config output
SHARED_LIB_PATHS := $(shell PKG_CONFIG_PATH="$(PKG_CONFIG_PATH)" pkg-config --static --libs libfolly | tr ' ' '\n' | grep '\.so' | sed 's|/[^/]*\.so$$||' | sort -u)
# Convert the paths into -rpath arguments
comma := ,
RPATH := $(patsubst %,-Wl$(comma)-rpath$(comma)%,$(SHARED_LIB_PATHS))

LDFLAGS += $(shell PKG_CONFIG_PATH="$(PKG_CONFIG_PATH)" pkg-config --static --libs libfolly)
LDFLAGS += $(shell PKG_CONFIG_PATH="$(PKG_CONFIG_PATH)" pkg-config --static --libs fmt)
LDFLAGS += $(RPATH)
LDFLAGS += -L$(LIB_DIR)/junction/lib
LDLIBS += -lcds -ljunction -lturf -lnuma

INCLUDES += -I$(realpath $(LIB_DIR)/cxxopt/include)
INCLUDES += $(shell PKG_CONFIG_PATH="$(PKG_CONFIG_PATH)" pkg-config --cflags fmt)
INCLUDES += $(shell PKG_CONFIG_PATH="$(PKG_CONFIG_PATH)" pkg-config --cflags libfolly)
INCLUDES += -I$(LIB_DIR)/junction/include
# INCLUDES += -I$(LIB_DIR)/tervel

# CXXFLAGS += -std=c++23 -O2 -g -pthread $(SANITIZE_FLAGS) $(INLCUDES)
CXXFLAGS += -std=c++23 -O2 -g -pthread $(INCLUDES)

SRCS = $(wildcard *.cc)
OBJS = $(subst .cc,.o,$(SRCS))

all: bench

bench: $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS) $(LDLIBS)

clean:
	-rm -f *.o bench

debug:
	@echo "RPATH = $(RPATH)"

.PHONY: all clean debug

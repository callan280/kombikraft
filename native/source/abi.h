/* Private isolated-VM probe for the captured Ramses 19 C++ ABI.
 * Uses exact exported symbols, no guessed firmware entry addresses.
 * Opaque aligned storage exceeds observed facade sizes; this is a research
 * adapter, not a production SDK or vehicle installation component.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <math.h>

static void *lib;
static void *sym(const char *name) {
    void *p=dlsym(lib,name);
    if (!p) { fprintf(stderr,"Missing export %s: %s\n",name,dlerror()); exit(3); }
    return p;
}
#define FN(type,name) ((type)sym(name))
typedef void (*CtorArgs)(void *,int,const char **);
typedef void (*CtorClient)(void *,const char *,void *);
typedef void (*Dtor)(void *);
typedef void (*CtorFile)(void *,const char *);
typedef void (*AddFile)(void *,const void *);
typedef void *(*LoadScene)(void *,const char *,const void *);
typedef uint64_t (*GetId)(const void *);
typedef void *(*Find)(void *,const char *);
typedef unsigned (*GetXYZ)(void *,float *,float *,float *);
typedef unsigned (*SetXYZ)(void *,float,float,float);
typedef unsigned (*SaveScene)(void *,const void *,const char *,const void *,int);
typedef unsigned (*Status)(void *);
typedef unsigned (*StatusMode)(void *,unsigned);
typedef unsigned (*SceneFlush)(void *,unsigned,uint64_t);
typedef unsigned (*CreateDisplay)(void *,const void *);
typedef unsigned (*MapScene)(void *,unsigned,uint64_t,int);
typedef unsigned (*SceneCommand)(void *,uint64_t);
typedef unsigned (*SetRect)(void *,int,int,unsigned,unsigned);
typedef unsigned (*SetUInt)(void *,unsigned);
typedef unsigned (*SetFour)(void *,float,float,float,float);
typedef unsigned (*SetSix)(void *,float,float,float,float,float,float);
typedef unsigned (*SetViewport)(void *,unsigned,unsigned,unsigned,unsigned);
typedef float (*GetFloat)(void *);
typedef unsigned (*SetVisibility)(void *,int);
typedef void (*RendererCtor)(void *,void *,const void *);
typedef union { long double alignment; unsigned char bytes[4096]; } Object;



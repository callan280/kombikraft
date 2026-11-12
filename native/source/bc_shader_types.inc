typedef struct{const char*name;unsigned width;const float*values;} BcAttribute;
typedef struct{const char*file;unsigned width,height;} BcSourceTexture;
typedef struct{const char*uniform;unsigned texture,wrapU,wrapV;} BcSourceSampler;

#include <stdbool.h>
#include "original_gauge_targets.inc"
typedef unsigned(*ReadUniformFloat)(const void*,const void*,float*);
typedef unsigned(*Read3)(const void*,const void*,float*,float*,float*);
typedef unsigned(*Read4)(const void*,const void*,float*,float*,float*,float*);
typedef void*(*GetObject)(const void*);
typedef bool(*GetBool)(const void*);
typedef unsigned(*GetType)(const void*);
typedef bool(*Contains)(const void*,const void*);
typedef unsigned(*Set4)(void*,const void*,float,float,float,float);
typedef struct{void*node,*app,*fx;Object input;float value[4];}Retained;
static Retained retained[GAUGE_COUNT];
static const char*get_transform[]={"","","_ZNK6ramses4Node14getTranslationERfS1_S1_","_ZNK6ramses4Node11getRotationERfS1_S1_","_ZNK6ramses4Node10getScalingERfS1_S1_"};
static void read_endpoint(unsigned i,Retained*s){
 const GaugeTarget*t=&gauge_targets[i];memset(s->value,0,sizeof(s->value));
 if(t->kind==1){s->value[0]=FN(GetBool,"_ZNK6ramses4Node13getVisibilityEv")(s->node)!=0;return;}
 if(t->kind>=2){check_status(FN(GetXYZ,get_transform[t->kind])(s->node,s->value,s->value+1,s->value+2),"originalPropertyRead");return;}
 if(t->type==4)check_status(FN(ReadUniformFloat,"_ZNK6ramses10Appearance18getInputValueFloatERKNS_12UniformInputERf")(s->app,&s->input,s->value),"originalFloatRead");
 else if(t->type==6)check_status(FN(Read3,"_ZNK6ramses10Appearance21getInputValueVector3fERKNS_12UniformInputERfS4_S4_")(s->app,&s->input,s->value,s->value+1,s->value+2),"originalVec3Read");
 else if(t->type==7)check_status(FN(Read4,"_ZNK6ramses10Appearance21getInputValueVector4fERKNS_12UniformInputERfS4_S4_S4_")(s->app,&s->input,s->value,s->value+1,s->value+2,s->value+3),"originalVec4Read");else exit(10);
}
static void resolve_endpoint(void*scene,unsigned i,Retained*s){
 const GaugeTarget*t=&gauge_targets[i];s->node=must(FN(Find,"_ZN6ramses5Scene16findObjectByNameEPKc")(scene,t->path),"originalControllerNode");
 if(!t->kind){s->app=must(FN(GetObject,"_ZN6ramses8MeshNode13getAppearanceEv")(s->node),"originalAppearance");s->fx=must(FN(GetObject,"_ZNK6ramses10Appearance9getEffectEv")(s->app),"originalEffect");FN(Dtor,"_ZN6ramses12UniformInputC1Ev")(&s->input);check_status(FN(FindInput,"_ZNK6ramses6Effect16findUniformInputEPKcRNS_12UniformInputE")(s->fx,t->uniform,&s->input),"originalUniform");if(FN(GetType,"_ZNK6ramses12UniformInput11getDataTypeEv")(&s->input)!=t->type)exit(10);}
 read_endpoint(i,s);
}
static void check_originals(void*scene){
 unsigned properties=0,uniforms=0;
 for(unsigned i=0;i<GAUGE_COUNT;i++){Retained after={0};resolve_endpoint(scene,i,&after);Retained*before=&retained[i];if(before->node!=after.node||before->app!=after.app||before->fx!=after.fx||memcmp(before->value,after.value,sizeof(before->value)))exit(11);if(gauge_targets[i].kind)properties++;else uniforms++;}
 printf("GRAFT_RETAINED {\"originalEndpoints\":%u,\"properties\":%u,\"uniforms\":%u,\"sameNodeAppearanceEffectPointers\":true,\"originalValuesByteIdentical\":true}\n",GAUGE_COUNT,properties,uniforms);
}
static void graft(void*client,void*scene){
 static const char*vs="attribute vec3 a_position;attribute vec2 a_uv;uniform float u_rotation;varying vec2 v_uv;void main(){vec2 p=vec2(a_position.x,-a_position.z);float c=cos(u_rotation),s=sin(u_rotation);p=vec2(c*p.x-s*p.y,s*p.x+c*p.y);gl_Position=vec4(p.x/960.0,p.y/360.0,0.0,1.0);v_uv=a_uv;}";
 static const char*fs="precision mediump float;uniform sampler2D u_texture;varying vec2 v_uv;void main(){gl_FragColor=texture2D(u_texture,v_uv);}";
 for(unsigned i=0;i<GAUGE_COUNT;i++)resolve_endpoint(scene,i,&retained[i]);
 void*main_group=must(FN(Find,"_ZN6ramses5Scene16findObjectByNameEPKc")(scene,"IC_main_RenderGroup"),"stockMainGroup");void*overlay=must(FN(Find,"_ZN6ramses5Scene16findObjectByNameEPKc")(scene,"IC_overlay_RenderGroup"),"stockOverlayGroup");
 void*group=must(FN(CreateNamed,"_ZN6ramses5Scene17createRenderGroupEPKc")(scene,"kombikraft/research/graft-group"),"sameSceneGroup");void*fx=custom_effect(client,vs,fs,"kombikraft/research/graft-effect");
 typedef struct{uint32_t size;const unsigned char*data;}MipData;typedef void*(*CreateTexture)(void*,unsigned,unsigned,unsigned,unsigned,const MipData*,_Bool,const unsigned*,const char*);
 unsigned char pixels[116*424*4];FILE*f=must(fopen("/mnt/scene-lab/f97/needle.rgba","rb"),"sourceNeedleFile");if(fread(pixels,1,sizeof(pixels),f)!=sizeof(pixels))exit(12);fclose(f);MipData mip={sizeof(pixels),pixels};void*texture=must(FN(CreateTexture,"_ZN6ramses12RamsesClient15createTexture2DEjjNS_14ETextureFormatEjPKNS_12MipLevelDataEbNS_18StronglyTypedValueIjNS_20resourceCacheFlagTagEEEPKc")(client,116,424,5,1,&mip,0,&no_cache,"kombikraft/research/graft-needle-texture"),"sourceNeedleUpload");void*sampler=must(FN(CreateSampler,"_ZN6ramses5Scene20createTextureSamplerENS_19ETextureAddressModeES1_NS_22ETextureSamplingMethodERKNS_9Texture2DEjPKc")(scene,0,0,2,texture,1,"kombikraft/research/graft-sampler"),"sameSceneSampler");
 unsigned n=sizeof(speedNeedle_positions)/sizeof(float)/3;uint16_t indices[256];if(n>256)exit(12);for(unsigned i=0;i<n;i++)indices[i]=i;
 void*mesh=custom_mesh(client,scene,group,fx,"kombikraft/research/graft-speed-needle",n,speedNeedle_positions,speedNeedle_uv,NULL,n,indices,0,sampler,0);
 if(FN(Contains,"_ZNK6ramses11RenderGroup16containsMeshNodeERKNS_8MeshNodeE")(main_group,mesh)||FN(Contains,"_ZNK6ramses11RenderGroup16containsMeshNodeERKNS_8MeshNodeE")(overlay,mesh)||!FN(Contains,"_ZNK6ramses11RenderGroup16containsMeshNodeERKNS_8MeshNodeE")(group,mesh))exit(12);
 void*app=must(FN(GetObject,"_ZN6ramses8MeshNode13getAppearanceEv")(mesh),"graftApp");Object input={0};FN(Dtor,"_ZN6ramses12UniformInputC1Ev")(&input);check_status(FN(FindInput,"_ZNK6ramses6Effect16findUniformInputEPKcRNS_12UniformInputE")(fx,"u_rotation",&input),"graftRotation");float values[]={0,.8943162965493129f,0};for(unsigned i=0;i<3;i++){float actual=-1;check_status(FN(SetFloat,"_ZN6ramses10Appearance18setInputValueFloatERKNS_12UniformInputEf")(app,&input,values[i]),"newComponentOnlyWrite");check_status(FN(ReadUniformFloat,"_ZNK6ramses10Appearance18getInputValueFloatERKNS_12UniformInputERf")(app,&input,&actual),"newComponentActualRead");if(actual!=values[i])exit(12);check_originals(scene);printf("GRAFT_COMPONENT {\"rotationRadians\":%.9g,\"sourceVertices\":%u,\"originalEndpointsUnchanged\":true}\n",actual,n);}
 check_status(FN(SceneFlush,"_ZN6ramses5Scene5flushENS_15ESceneFlushModeEm")(scene,1,1),"sameSceneFlush");check_originals(scene);
 if(FN(Find,"_ZN6ramses5Scene16findObjectByNameEPKc")(scene,"kombikraft/research/graft-speed-needle")!=mesh)exit(12);
 printf("GRAFT_COMPLETE {\"sceneId\":%llu,\"sameScenePointer\":true,\"appendedOriginalF97Mesh\":true,\"originalEndpointsRetained\":%u,\"controllerExecutionRepeated\":false,\"originalSceneSettersCalled\":false,\"newObjectSettersCalled\":true,\"customGroupAddedToOriginalPass\":false,\"published\":false,\"mapped\":false,\"ownerEntryProved\":false,\"installationAllowed\":false}\n",(unsigned long long)FN(GetId,"_ZNK6ramses5Scene10getSceneIdEv")(scene),GAUGE_COUNT);
}

#include "underlay_body.inc"

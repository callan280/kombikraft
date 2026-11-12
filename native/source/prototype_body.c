typedef unsigned (*SetVec4)(void *,const void *,float,float,float,float);
typedef unsigned (*ReadFloat)(const void *,const void *,float *);
typedef struct {uint32_t size;const unsigned char *data;} MipData;
typedef void *(*CreateTexture)(void *,unsigned,unsigned,unsigned,unsigned,const MipData *,_Bool,const unsigned *,const char *);
static void *f97_sampler(void *client,void *scene,const char *key){
 const F97Texture*lists[]={f97_textures,v2_textures,v3_textures,fuel_textures,gear_textures};const unsigned counts[]={sizeof(f97_textures)/sizeof(f97_textures[0]),sizeof(v2_textures)/sizeof(v2_textures[0]),sizeof(v3_textures)/sizeof(v3_textures[0]),sizeof(fuel_textures)/sizeof(fuel_textures[0]),sizeof(gear_textures)/sizeof(gear_textures[0])};
 for(unsigned set=0;set<5;set++){for(unsigned i=0;i<counts[set];i++){if(strcmp(key,lists[set][i].key))continue;
  const F97Texture*t=&lists[set][i];char path[300];snprintf(path,sizeof(path),"/mnt/scene-lab/f97/%s",t->file);FILE*f=must(fopen(path,"rb"),"textureFile");unsigned bytes=t->width*t->height*4;unsigned char*p=must(malloc(bytes),"textureMemory");if(fread(p,1,bytes,f)!=bytes){fputs("Texture read failed\n",stderr);exit(8);}fclose(f);MipData mip={bytes,p};void*tex=must(FN(CreateTexture,"_ZN6ramses12RamsesClient15createTexture2DEjjNS_14ETextureFormatEjPKNS_12MipLevelDataEbNS_18StronglyTypedValueIjNS_20resourceCacheFlagTagEEEPKc")(client,t->width,t->height,5,1,&mip,0,&no_cache,key),"textureUpload");free(p);return must(FN(CreateSampler,"_ZN6ramses5Scene20createTextureSamplerENS_19ETextureAddressModeES1_NS_22ETextureSamplingMethodERKNS_9Texture2DEjPKc")(scene,0,0,2,tex,1,key),"sampler");
 }}
 fprintf(stderr,"Unknown source texture:%s\n",key);exit(8);
}
static const char*f97_vs="attribute vec3 a_position;attribute vec2 a_uv;uniform vec2 u_center;uniform float u_scale;uniform float u_rotation;varying vec2 v_uv;varying vec2 v_pixel;void main(){vec2 p=vec2(a_position.x,-a_position.z);float c=cos(u_rotation),s=sin(u_rotation);p=vec2(c*p.x-s*p.y,s*p.x+c*p.y)*u_scale+u_center;gl_Position=vec4(p.x/960.0-1.0,1.0-p.y/360.0,0.0,1.0);v_uv=a_uv;v_pixel=p;}";
static const char*f97_fs="precision mediump float;uniform sampler2D u_texture;uniform vec4 u_tint;uniform float u_clipY;varying vec2 v_uv;varying vec2 v_pixel;void main(){if(v_pixel.y>u_clipY)discard;gl_FragColor=texture2D(u_texture,v_uv)*u_tint;}";
typedef struct{void*app,*mesh;Object rotation;Object tint;int needle;int palette;float baseAngle;float sweep;int signal;const char*name;} F97Part;
static F97Part f97_parts[128];static unsigned f97_count;
static void f97_input(void*fx,const char*name,Object*input){FN(Dtor,"_ZN6ramses12UniformInputC1Ev")(input);check_status(FN(FindInput,"_ZNK6ramses6Effect16findUniformInputEPKcRNS_12UniformInputE")(fx,name,input),name);}
static void f97_part(void*client,void*scene,void*group,void*fx,const char*name,unsigned count,float*pos,float*uv,const char*texture,float cx,float cy,float radius,int order,int signal,int tint){
 uint16_t*indices=must(malloc(count*sizeof(uint16_t)),"indices");for(unsigned i=0;i<count;i++)indices[i]=i;
 const char*needleNames[]={"f40/main-speed/needle","f40/main-rpm/needle","f40/mini-oil/needle","f40/mini-boost/needle","f40/mini-coolant/needle"};if(signal>=0)name=needleNames[signal];
 void*mesh=custom_mesh(client,scene,group,fx,name,count,pos,uv,NULL,count,indices,0,f97_sampler(client,scene,texture),order);free(indices);
 typedef void*(*GetAppearance)(void*);void*app=must(FN(GetAppearance,"_ZN6ramses8MeshNode13getAppearanceEv")(mesh),"appearanceGet");
 Object input={0};f97_input(fx,"u_center",&input);check_status(FN(SetVec2,"_ZN6ramses10Appearance21setInputValueVector2fERKNS_12UniformInputEff")(app,&input,cx,cy),"center");
 f97_input(fx,"u_scale",&input);check_status(FN(SetFloat,"_ZN6ramses10Appearance18setInputValueFloatERKNS_12UniformInputEf")(app,&input,radius/340.0f),"scale");
 f97_input(fx,"u_clipY",&input);check_status(FN(SetFloat,"_ZN6ramses10Appearance18setInputValueFloatERKNS_12UniformInputEf")(app,&input,680),"gaugeClip680");
 F97Part*p=&f97_parts[f97_count++];p->app=app;p->mesh=mesh;p->name=name;p->signal=signal;p->needle=signal>=0;p->palette=tint;p->baseAngle=signal>1?14*3.14159265359f/180:0;p->sweep=(signal>1?260:234)*3.14159265359f/180;
 f97_input(fx,"u_rotation",&p->rotation);check_status(FN(SetFloat,"_ZN6ramses10Appearance18setInputValueFloatERKNS_12UniformInputEf")(app,&p->rotation,p->baseAngle),"rotation");
 f97_input(fx,"u_tint",&p->tint);check_status(FN(SetVec4,"_ZN6ramses10Appearance21setInputValueVector4fERKNS_12UniformInputEffff")(app,&p->tint,tint?1.6f:1.0f,tint?.768f:1.0f,tint?.192f:1.0f,1),"tint");
 printf("F97_SOURCE_MESH name=%s vertices=%u center=%.0f,%.0f radius=%.0f\n",name,count,cx,cy,radius);
}
static void v2_part(void*client,void*scene,void*group,void*fx,const char*name,unsigned count,float*pos,float*uv,const char*texture,float cx,float cy,float radius,int order,float red,float green,float blue,float alpha){
 f97_part(client,scene,group,fx,name,count,pos,uv,texture,cx,cy,radius,order,-1,0);F97Part*p=&f97_parts[f97_count-1];check_status(FN(SetVec4,"_ZN6ramses10Appearance21setInputValueVector4fERKNS_12UniformInputEffff")(p->app,&p->tint,red,green,blue,alpha),"customCompositionColor");
}
#define V2PART(k,t,x,y,r,order,red,green,blue,alpha) v2_part(client,scene,group,fx,#k,sizeof(k##_positions)/sizeof(float)/3,k##_positions,k##_uv,t,x,y,r,order,red,green,blue,alpha)
#define PART(k,t,x,y,r,order,signal,tint) f97_part(client,scene,group,fx,#k,sizeof(k##_positions)/sizeof(float)/3,k##_positions,k##_uv,t,x,y,r,order,signal,tint)
static int cc_selected;
static int v10_traction,v10_clock_source,v10_clock_hour,v10_clock_minute;static void draw_v10_clock(int*verified);
static int semantic_active;static int semantic_mode=-1;static void apply_semantic(int*verified);
static unsigned apply_gear(int*verified);
#include "footer_runtime.inc"
#include "gear_runtime.inc"
typedef unsigned (*CcMatrix)(void*,const void*,const float*);
#include "bc_runtime.inc"
#include "cc_runtime.inc"
#include "semantic_runtime.inc"
#include "axis_probe_runtime.inc"
#include "status_v10_runtime.inc"
static void*build_f97(void*client){
 Object config={0};FN(Dtor,"_ZN6ramses11SceneConfigC1Ev")(&config);void*scene=must(FN(CreateScene,"_ZN6ramses12RamsesClient11createSceneEmRKNS_11SceneConfigEPKc")(client,501,&config,"isolated-F97-source-geometry-custom-material"),"scene");
 void*camera=must(FN(CreateNamed,"_ZN6ramses5Scene24createOrthographicCameraEPKc")(scene,"own-camera"),"camera");check_status(FN(SetViewport,"_ZN6ramses11LocalCamera11setViewportEjjjj")(camera,0,0,1920,720),"viewport");check_status(FN(SetSix,"_ZN6ramses11LocalCamera10setFrustumEffffff")(camera,-1,1,-1,1,.1,10),"frustum");
 void*pass=must(FN(CreateNamed,"_ZN6ramses5Scene16createRenderPassEPKc")(scene,"own-pass"),"pass");void*group=must(FN(CreateNamed,"_ZN6ramses5Scene17createRenderGroupEPKc")(scene,"own-group"),"group");check_status(FN(BindObj,"_ZN6ramses10RenderPass9setCameraERKNS_6CameraE")(pass,camera),"camera");check_status(FN(AddRender,"_ZN6ramses10RenderPass14addRenderGroupERKNS_11RenderGroupEi")(pass,group,0),"group");
 void*fx=custom_effect(client,f97_vs,f97_fs,"custom-unlit-f97-source-sampling");
 PART(speedInner,"speedInner",330,375,330,1,-1,1);PART(speedRing,"ring",330,375,330,2,-1,1);PART(speedScale,"speedScale",330,375,330,3,-1,0);PART(speedNumbers,"speedNumbers",330,375,330,4,-1,0);PART(speedNeedle,"needle",330,375,330,360,0,0);
 PART(rpmInner,"rpmInner",1590,375,330,11,-1,1);PART(rpmRing,"ring",1590,375,330,12,-1,1);PART(rpmScale,"rpmScale",1590,375,330,13,-1,0);PART(rpmNumbers,"rpmNumbers",1590,375,330,14,-1,0);PART(rpmNeedle,"needle",1590,375,330,361,1,0);
 PART(speedInner,"speedInner",740,160,80,101,-1,1);PART(speedNeedle,"needle",740,160,80,106,2,0);
 PART(speedInner,"speedInner",960,160,80,131,-1,1);PART(speedNeedle,"needle",960,160,80,136,3,0);
 PART(speedInner,"speedInner",1180,160,80,161,-1,1);PART(speedNeedle,"needle",1180,160,80,166,4,0);
 #include "composition_parts.inc"
 build_footer(client,scene,group,fx);build_gear(client,scene,group,fx);build_bc(client,scene);build_cc(client,scene,group);build_semantic(client,scene,group);
 printf("NATIVE_F97_CREATED {\"sceneId\":501,\"meshes\":%u,\"sourcePackage\":\"c81132e977a9de407997893fd0a177f1c969ddd8732efbac6058b306d4a05864\",\"customUnlitShader\":true,\"originalCompiledShaderExecuted\":false}\n",f97_count+fuel_count+bc_sprite_count+bc_source_count+cc_count+19);return scene;
}
static void process_f97(void*scene){
 static unsigned long long last=0;FILE*f=fopen("/tmp/native-f97-request","r");if(!f)return;unsigned long long id=0;float values[5];int mode=0;int got=fscanf(f,"%llu %f %f %f %f %f %d",&id,&values[0],&values[1],&values[2],&values[3],&values[4],&mode);fclose(f);if(got!=7||id<=last)return;last=id;if(semantic_active){printf("NATIVE_F97_REJECT semantic-active id=%llu\n",id);return;}
 int valid=mode>=0&&mode<=2;for(unsigned i=0;i<5;i++)valid&=isfinite(values[i])&&values[i]>=0&&values[i]<=1;if(!valid){printf("NATIVE_F97_REJECT id=%llu\n",id);return;}
 const float palette[3][3]={{1,.48,.12},{1,.1,.15},{.18,.57,1}};int verified=1;float rotations[5]={0};
 for(unsigned i=0;i<f97_count;i++){F97Part*p=&f97_parts[i];if(p->needle){float expected=p->baseAngle+values[p->signal]*p->sweep;check_status(FN(SetFloat,"_ZN6ramses10Appearance18setInputValueFloatERKNS_12UniformInputEf")(p->app,&p->rotation,expected),"requestedRotation");float after=0;verified&=!FN(ReadFloat,"_ZNK6ramses10Appearance18getInputValueFloatERKNS_12UniformInputERf")(p->app,&p->rotation,&after)&&fabsf(after-expected)<.000001f;rotations[p->signal]=after;}if(p->palette)check_status(FN(SetVec4,"_ZN6ramses10Appearance21setInputValueVector4fERKNS_12UniformInputEffff")(p->app,&p->tint,palette[mode][0]*1.6f,palette[mode][1]*1.6f,palette[mode][2]*1.6f,1),"requestedTint");}
 footer_mode=mode;apply_footer(&verified);apply_bc(&verified);
 unsigned flush=FN(SceneFlush,"_ZN6ramses5Scene5flushENS_15ESceneFlushModeEm")(scene,1,id+100);
 printf("NATIVE_F97_ACK {\"id\":%llu,\"readbackVerified\":%s,\"flushStatus\":%u,\"mode\":%d,\"rotations\":[%.9g,%.9g,%.9g,%.9g,%.9g]}\n",id,verified?"true":"false",flush,mode,rotations[0],rotations[1],rotations[2],rotations[3],rotations[4]);
}
int main(void){setvbuf(stdout,NULL,_IONBF,0);char marker[4096]={0};FILE*f=fopen("/proc/cmdline","r");if(f){fread(marker,1,sizeof(marker)-1,f);fclose(f);}if(!strstr(marker,"idemu.role=native-f97")){fputs("Own isolated VM required\n",stderr);return 2;}
 lib=dlopen("/mnt/scene-lab/lib/libramses-shared-lib-wayland-ivi-egl-es-3-0.so.19.0",RTLD_NOW|RTLD_GLOBAL);if(!lib){fprintf(stderr,"dlopen:%s\n",dlerror());return 3;}
 Object framework={0},client={0};const char*args[]={"native-f97",NULL};FN(CtorArgs,"_ZN6ramses15RamsesFrameworkC1EiPPKc")(&framework,1,args);FN(CtorClient,"_ZN6ramses12RamsesClientC1EPKcRNS_15RamsesFrameworkE")(&client,"isolated-F97-custom-material",&framework);void*scene=build_f97(&client);
 Object rc={0},renderer={0},dc={0};FN(CtorArgs,"_ZN6ramses14RendererConfigC1EiPKPKc")(&rc,1,args);FN(RendererCtor,"_ZN6ramses14RamsesRendererC1ERNS_15RamsesFrameworkERKNS_14RendererConfigE")(&renderer,&framework,&rc);FN(CtorArgs,"_ZN6ramses13DisplayConfigC1EiPKPKc")(&dc,1,args);FN(SetRect,"_ZN6ramses13DisplayConfig18setWindowRectangleEiijj")(&dc,0,0,1920,720);FN(SetUInt,"_ZN6ramses13DisplayConfig22setWaylandIviSurfaceIDEj")(&dc,15001);FN(SetUInt,"_ZN6ramses13DisplayConfig20setWaylandIviLayerIDEj")(&dc,15000);FN(SetFour,"_ZN6ramses13DisplayConfig24setPerspectiveProjectionEffff")(&dc,17.06f,1920.0f/720,1,10000);check_status(FN(Status,"_ZN6ramses15RamsesFramework7connectEv")(&framework),"connect");unsigned display=FN(CreateDisplay,"_ZN6ramses14RamsesRenderer13createDisplayERKNS_13DisplayConfigE")(&renderer,&dc);check_status(FN(StatusMode,"_ZN6ramses5Scene7publishENS_21EScenePublicationModeE")(scene,1),"publish");FN(SceneFlush,"_ZN6ramses5Scene5flushENS_15ESceneFlushModeEm")(scene,1,1);
 for(unsigned frame=0;frame<0xffffffffu;frame++){if(frame%10==0){process_f97(scene);process_footer(scene);process_gear(scene);process_cc(scene);process_bc(scene);process_semantic(scene);process_semantic_state(scene);tick_semantic_replay(scene);process_axis_probe(scene);process_status_v10(scene);process_clock_v10(scene);}if(semantic_active&&frame%10==0){int sem_ok=1;apply_semantic(&sem_ok);if(!sem_ok)exit(8);check_status(FN(SceneFlush,"_ZN6ramses5Scene5flushENS_15ESceneFlushModeEm")(scene,1,0),"semantic reservation publication");}tick_bc_marquee(scene);if(frame==10)FN(SceneCommand,"_ZN6ramses14RamsesRenderer14subscribeSceneEm")(&renderer,501);if(frame==40)FN(MapScene,"_ZN6ramses14RamsesRenderer8mapSceneEjmi")(&renderer,display,501,0);if(frame>=80&&frame%120==80)FN(SceneCommand,"_ZN6ramses14RamsesRenderer9showSceneEm")(&renderer,501);FN(Status,"_ZN6ramses14RamsesRenderer5flushEv")(&renderer);FN(Status,"_ZN6ramses14RamsesRenderer9doOneLoopEv")(&renderer);if(frame%120==0)printf("NATIVE_F97_LOOP=%u\n",frame);usleep(16666);}return 0;}

/* New offline layout geometry in native Ramses scenes. No factory graph edits. */
typedef void *(*CreateNamed)(void *,const char *);
typedef void *(*CreateWith)(void *,const void *,const char *);
typedef void *(*CreateScene)(void *,uint64_t,const void *,const char *);
typedef void *(*CreateEffect)(void *,const void *,const unsigned *,const char *);
typedef void *(*CreateArray)(void *,unsigned,const void *,const unsigned *,const char *);
typedef unsigned (*SetString)(void *,const char *);
typedef unsigned (*FindInput)(const void *,const char *,void *);
typedef unsigned (*BindBuffer)(void *,const void *,const void *,unsigned);
typedef unsigned (*BindObj)(void *,const void *);
typedef unsigned (*AddRender)(void *,const void *,int);
typedef unsigned (*SetFloat)(void *,const void *,float);
typedef unsigned (*Blend4)(void *,unsigned,unsigned,unsigned,unsigned);
typedef unsigned (*Blend2)(void *,unsigned,unsigned);
typedef void *(*CreateSampler)(void *,unsigned,unsigned,unsigned,const void *,unsigned,const char *);
typedef unsigned (*SetTexture)(void *,const void *,const void *);
static void *preview_scenes[4];
static int building_no_map;
static unsigned mesh_serial;
static const unsigned no_cache=0;
typedef unsigned (*SetVec2)(void *,const void *,float,float);
typedef struct {void *app;void *scene;Object angle;float original;float side;} NeedleControl;
static NeedleControl native_needles[4];static unsigned native_needle_count;
static int current_variant;
static void check_status(unsigned s,const char *what){if(s){fprintf(stderr,"CUSTOM_NATIVE_FAILURE %s status%u\n",what,s);exit(8);}}
static void *must(void *p,const char *what){if(!p){fprintf(stderr,"CUSTOM_NATIVE_FAILURE %s NULL\n",what);exit(8);}return p;}
static void *custom_effect(void *client,const char *vs,const char *fs,const char *name){
 Object desc={0};FN(Dtor,"_ZN6ramses17EffectDescriptionC1Ev")(&desc);
 check_status(FN(SetString,"_ZN6ramses17EffectDescription15setVertexShaderEPKc")(&desc,vs),"vertexSource");
 check_status(FN(SetString,"_ZN6ramses17EffectDescription17setFragmentShaderEPKc")(&desc,fs),"fragmentSource");
 return must(FN(CreateEffect,"_ZN6ramses12RamsesClient12createEffectERKNS_17EffectDescriptionENS_18StronglyTypedValueIjNS_20resourceCacheFlagTagEEEPKc")(client,&desc,&no_cache,name),"createEffect");
}
static void *custom_mesh(void *client,void *scene,void *group,void *fx,const char *name,unsigned nv,float *positions,float *uv,float *colors,unsigned ni,uint16_t *indices,float side,void *sampler,int order){
 void *pos=must(FN(CreateArray,"_ZN6ramses12RamsesClient24createConstVector3fArrayEjPKfNS_18StronglyTypedValueIjNS_20resourceCacheFlagTagEEEPKc")(client,nv,positions,&no_cache,name),"positions");
 void *idx=must(FN(CreateArray,"_ZN6ramses12RamsesClient22createConstUInt16ArrayEjPKtNS_18StronglyTypedValueIjNS_20resourceCacheFlagTagEEEPKc")(client,ni,indices,&no_cache,name),"indices");
 void *geo=must(FN(CreateWith,"_ZN6ramses5Scene21createGeometryBindingERKNS_6EffectEPKc")(scene,fx,name),"geometry");
 void *app=must(FN(CreateWith,"_ZN6ramses5Scene16createAppearanceERKNS_6EffectEPKc")(scene,fx,name),"appearance");
 void *mesh=must(FN(CreateNamed,"_ZN6ramses5Scene14createMeshNodeEPKc")(scene,name),"mesh");
 Object input={0};FN(Dtor,"_ZN6ramses14AttributeInputC1Ev")(&input);
 check_status(FN(FindInput,"_ZNK6ramses6Effect18findAttributeInputEPKcRNS_14AttributeInputE")(fx,"a_position",&input),"positionInput");
 check_status(FN(BindBuffer,"_ZN6ramses15GeometryBinding14setInputBufferERKNS_14AttributeInputERKNS_13Vector3fArrayEj")(geo,&input,pos,0),"positionBinding");
 if(uv){void *r=must(FN(CreateArray,"_ZN6ramses12RamsesClient24createConstVector2fArrayEjPKfNS_18StronglyTypedValueIjNS_20resourceCacheFlagTagEEEPKc")(client,nv,uv,&no_cache,name),"uvArray");check_status(FN(FindInput,"_ZNK6ramses6Effect18findAttributeInputEPKcRNS_14AttributeInputE")(fx,"a_uv",&input),"uvInput");check_status(FN(BindBuffer,"_ZN6ramses15GeometryBinding14setInputBufferERKNS_14AttributeInputERKNS_13Vector2fArrayEj")(geo,&input,r,0),"uvBinding");}
 if(colors){void *r=must(FN(CreateArray,"_ZN6ramses12RamsesClient24createConstVector4fArrayEjPKfNS_18StronglyTypedValueIjNS_20resourceCacheFlagTagEEEPKc")(client,nv,colors,&no_cache,name),"colorArray");check_status(FN(FindInput,"_ZNK6ramses6Effect18findAttributeInputEPKcRNS_14AttributeInputE")(fx,"a_color",&input),"colorInput");check_status(FN(BindBuffer,"_ZN6ramses15GeometryBinding14setInputBufferERKNS_14AttributeInputERKNS_13Vector4fArrayEj")(geo,&input,r,0),"colorBinding");}
 check_status(FN(BindObj,"_ZN6ramses15GeometryBinding10setIndicesERKNS_11UInt16ArrayE")(geo,idx),"indexBinding");
 check_status(FN(BindObj,"_ZN6ramses8MeshNode13setAppearanceERNS_10AppearanceE")(mesh,app),"meshAppearance");
 check_status(FN(BindObj,"_ZN6ramses8MeshNode18setGeometryBindingERNS_15GeometryBindingE")(mesh,geo),"meshGeometry");
 check_status(FN(SetUInt,"_ZN6ramses8MeshNode13setIndexCountEj")(mesh,ni),"indexCount");
 check_status(FN(StatusMode,"_ZN6ramses10Appearance16setDepthFunctionENS_10EDepthFuncE")(app,0),"depthDisabled");
 check_status(FN(StatusMode,"_ZN6ramses10Appearance13setDepthWriteEb")(app,0),"depthWrite");
 check_status(FN(StatusMode,"_ZN6ramses10Appearance14setCullingModeENS_9ECullModeE")(app,0),"cullingDisabled");
 check_status(FN(Blend4,"_ZN6ramses10Appearance18setBlendingFactorsENS_12EBlendFactorES1_S1_S1_")(app,2,3,1,3),"blendFactors");
 check_status(FN(Blend2,"_ZN6ramses10Appearance21setBlendingOperationsENS_15EBlendOperationES1_")(app,1,1),"blendAdd");
 Object uniform={0};FN(Dtor,"_ZN6ramses12UniformInputC1Ev")(&uniform);
 if(!FN(FindInput,"_ZNK6ramses6Effect16findUniformInputEPKcRNS_12UniformInputE")(fx,"u_side",&uniform))check_status(FN(SetFloat,"_ZN6ramses10Appearance18setInputValueFloatERKNS_12UniformInputEf")(app,&uniform,building_no_map?0:side),"sideUniform");
 if(sampler){check_status(FN(FindInput,"_ZNK6ramses6Effect16findUniformInputEPKcRNS_12UniformInputE")(fx,"u_texture",&uniform),"textureUniform");check_status(FN(SetTexture,"_ZN6ramses10Appearance15setInputTextureERKNS_12UniformInputERKNS_14TextureSamplerE")(app,&uniform,sampler),"textureBinding");}
 if(!FN(FindInput,"_ZNK6ramses6Effect16findUniformInputEPKcRNS_12UniformInputE")(fx,"u_angle",&uniform)){
  float angle=(side<0?72.0f/260:3.5f/8)*4.71238898f;
  check_status(FN(SetFloat,"_ZN6ramses10Appearance18setInputValueFloatERKNS_12UniformInputEf")(app,&uniform,angle),"needleAngle");
  if(native_needle_count<4){NeedleControl *n=&native_needles[native_needle_count++];n->app=app;n->scene=scene;n->angle=uniform;n->original=angle;n->side=side;}
  Object centre={0};FN(Dtor,"_ZN6ramses12UniformInputC1Ev")(&centre);check_status(FN(FindInput,"_ZNK6ramses6Effect16findUniformInputEPKcRNS_12UniformInputE")(fx,"u_centre",&centre),"needleCentre");check_status(FN(SetVec2,"_ZN6ramses10Appearance21setInputValueVector2fERKNS_12UniformInputEff")(app,&centre,side<0?330:1590,350),"needleCentreValue");
 }
 check_status(FN(AddRender,"_ZN6ramses11RenderGroup11addMeshNodeERKNS_8MeshNodeEi")(group,mesh,order),"addMesh");mesh_serial++;return mesh;
}

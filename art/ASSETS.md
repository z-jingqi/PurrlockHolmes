# 茶点器物 · Afternoon Tea

`room.blend` 的 Blender Collection Assets（可通过 File → Append → Collection 或 Asset Browser 复用）：

| ID | 资产集合 | 几何特征 |
|---|---|---|
| cup | Tea · Celadon cup | 内壁、有厚度的杯口、弧形拉坯把手、足圈与茶面 |
| saucer | Tea · Porcelain saucer | 凹盘、足圈、青釉细边 |
| plate | Tea · Petal plate | 浅盘膛、花瓣轮廓、淡桃釉环 |
| fork | Tea · Satin dessert fork | 弧形叉颈、带浅凹的四齿叉头与缎面不锈钢 |
| bowl | Tea · Blush bowl | 内壁、裙足、花瓣口沿及釉线 |
| teapot | Tea · Moon teapot | 可分离釉盖、中空壶嘴、收细的弯柄与壶足 |

Z 轴向上，局部原点是容器落脚中心；关卡内各自用 Collection Instance 摆位，模型几何与摆放分开。分类为 `tableware`，不是按某个关卡绑死的文件。资产不依赖外部图片。

保存编辑后的 .blend，再生成运行时素材：

```sh
PURRLOCK_BAKE_DIR=/tmp/purrlock-bake blender -b art/room.blend --python art/export_room.py
python3 art/pack_tea.py /tmp/purrlock-bake
PURRLOCK_BAKE_DIR=/tmp/purrlock-bake blender -b art/room.blend --python art/asset_previews.py
```

更新房间底图时，还要从这次生成的、包含小熊的原图重建小熊的独立 3D 视口。不要把已移除熊的底图作为参考输入：

```sh
cp assets/room.webp /tmp/purrlock-bake/room-with-teddy.webp
PURRLOCK_BEAR_STAGE=/tmp/purrlock-bake/bear blender -b art/room.blend --python art/export_bear.py
python3 art/pack_bear.py /tmp/purrlock-bake/bear /tmp/purrlock-bake/room-with-teddy.webp
```

`assets/teddy.glb` 保留真实几何、可编辑材质与地面原点，换镜头可以复用。第一关的专用显示把已核准视角的光色投到模型上，只由网格计算轮廓。清空底图时保留接触影并无损写入，其余区域保持原像素。`pack_bear.py` 需要 NumPy 与 Pillow。


打包需要 Pillow；有 OpenCV 时优先保留轮廓做彩色去噪，没有时使用轻量中值去噪。自带 OpenImageDenoise 的 Blender 可以加 `PURRLOCK_OIDN=1` 渲染，并在打包时传 `--already-denoised`。若要从程序化模型重建源文件，可运行 `blender -b --python art/build_room.py`，会覆盖当前 `room.blend`。

## 茶室陈设 · Room props

| ID | 资产集合 | 结构与材质 | 参考质量 |
|---|---|---|---:|
| clay_planter | Room · Terracotta planter | 有厚度的陶壁、卷口、独立接水碟，哑光赤陶 | 0.82 kg |
| celadon_planter | Room · Celadon planter | 石陶底足、釉面、内壁和车削环线 | 0.73 kg |
| rubber_plant | Room · Rubber plant | 弯曲叶面、叶脉、枝茎及有层次的土面 | 0.29 kg |
| lance_plant | Room · Lanceleaf plant | 窄叶、根部与不同弧度的叶柄 | 0.23 kg |
| felt_slippers | Room · Felt slippers | 左右脚楦、橡胶底、抓绒内里、包边与缝线 | 0.34 kg / 双 |
| reed_basket | Room · Linen-lined rattan basket | 藤条上下交织、卷边及蓝色亚麻衬布 | 0.57 kg |

质量是供以后给刚体设定质量的参考值，存在 Blender 集合的 `mass_kg` 中，缩放实例时应重新评估。第一关仍然仅收集餐具：固定家具、玩具及拖鞋住在同一张底图里；仅猫、两株植物的叶片和三只气球会响应点击。叶片分别以自己的叶柄接点转动，猫在独立的固定机位视口中以真实 3D 模型抬头、眨眼，气球在 Blender 里有独立的哑光乳胶球体、折叠气嘴与棉绳。运行时气球用不含绳子的透明图，棉绳用 Godot 实时绘制为独立柔性曲线，始终连接气嘴和 Blender 小熊爪的系绳点。视角和渲染位置由 `room-layout.json` 中间数据传给打包器，不需在引擎中手摆模型。

焦点物件的软布靠枕与乳胶气球由 `art/hero_props.py` 建立；整屋可见物件的分类和落点见 [第一关清单](../docs/level-01-inventory.md)。叉子在 Blender 中以 4 倍尺寸烘焙，打包器保留 2 倍显示纹理与原尺寸点击遮罩。

## 单独更新气球 · Balloons

只替换三只气球和各自的气嘴、棉绳，不重排房间或覆盖叉子。Blender 中的独立绳对象供检查，故意不烘焙到背景或球体图里：

```sh
PURRLOCK_BALLOON_STAGE=/tmp/purrlock-balloons PURRLOCK_SAVE_BALLOONS=1 blender -b art/room.blend --python art/revise_balloons.py
python3 art/pack_balloons.py /tmp/purrlock-balloons
```

## 奶油猫 · Cream cat

运行时网格是 `assets/cat.glb`：耳朵、脸、猫爪和领结均有独立的立体结构，姿态纹理贴在网格 UV 而非屏幕上。点击时头部转动，闭眼纹理随面部一起移动。只有在动画期间更新猫的独立视口；原参考垫子不进入关卡。换机位复用时应为新视角制作材质，不能把只校准过正面机位的光色贴图当作完整 PBR 材质。

如需重建，使用已拟合的猫模型源和带边缘延展的参考 UV 图。源文件无需作为游戏资源提交。先重新打包主场景并重建小熊底图，再运行：

```sh
blender -b fitted-cat.blend --python art/export_cat.py
PURRLOCK_CAT_STAGE=/tmp/purrlock-bake blender -b art/room.blend --python art/clear_room_cat.py
python3 art/pack_cat_room.py /tmp/purrlock-bake/sofa-clear.png cat-reference-uv.png
```

## 高清底图与单独更新餐叉

只重建叉子而不改其他摆位：

```sh
PURRLOCK_SAVE_FORK=1 PURRLOCK_FORK_STAGE=/tmp/purrlock-fork blender -b art/room.blend --python art/revise_fork.py
python3 art/pack_fork.py /tmp/purrlock-fork
```

全量导出房间时，先打包其他素材并更新独立模型与相关图。最后用高清底图替换初稿，背景不含动态道具，保留接触影：

```sh
PURRLOCK_BAKE_DIR=/tmp/purrlock-room-hd PURRLOCK_REFRESH_BACKGROUND_ONLY=1 PURRLOCK_HD_PLATE=1 PURRLOCK_SAMPLES=164 blender -b art/room.blend --python art/export_room.py
python3 art/pack_hd_plate.py /tmp/purrlock-room-hd/room.png
```

## 餐叉造型

`fork_profile.py` 分别记录正面宽度和侧面高度：握柄细、接口逐渐放宽，叉颈下探至叉头根部，四根直齿沿同一斜面向上伸出。叉子是单件有厚度的网格，使用暖色拉丝钢材质。单独导出时，打包器按新侧面高度调整接触影，同一轮廓用于生成高清显示图和点击遮罩。对照图、试渲染和测试文件不入库。

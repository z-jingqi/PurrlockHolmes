# 茶点器物 · Afternoon Tea

`room.blend` 的 Blender Collection Assets（可通过 File → Append → Collection 或 Asset Browser 复用）：

| ID | 资产集合 | 几何特征 |
|---|---|---|
| cup | Tea · Celadon cup | 内壁、有厚度的杯口、弧形拉坯把手、足圈与茶面 |
| saucer | Tea · Porcelain saucer | 凹盘、足圈、青釉细边 |
| plate | Tea · Petal plate | 浅盘膛、花瓣轮廓、淡桃釉环 |
| fork | Tea · Satin dessert fork | 冲压手柄、四根收尖叉齿、浅刻握柄 |
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

质量是供以后给刚体设定质量的参考值，存在 Blender 集合的 `mass_kg` 中，缩放实例时应重新评估。第一关仍然仅收集餐具：固定家具、玩具及拖鞋住在同一张底图里；仅猫、两株植物的叶片和三只气球会响应点击。叶片分别以自己的叶柄接点转动，猫在独立的固定机位视口中以真实 3D 模型抬头、眨眼，乳胶气球是透明图，绳子是 Godot 绘制的柔性曲线，落点来自 Blender 的小熊爪上锚点。视角和渲染位置由 `room-layout.json` 中间数据传给打包器，不需在引擎中手摆模型。

焦点物件的软布靠枕与乳胶气球由 `art/hero_props.py` 建立；整屋可见物件的分类和落点见 [第一关清单](../docs/level-01-inventory.md)。叉子在 Blender 中以 2 倍尺寸烘焙，由打包器缩到同一画布尺寸。

## 奶油猫 · Cream cat

运行时网格是 `assets/cat.glb`：耳朵、脸、猫爪和领结均有独立的立体结构，姿态纹理贴在网格 UV 而非屏幕上。点击时头部转动，闭眼纹理随面部一起移动。只有在动画期间更新猫的独立视口；原参考垫子不进入关卡。换机位复用时应为新视角制作材质，不能把只校准过正面机位的光色贴图当作完整 PBR 材质。

如需重建，使用已拟合的猫模型源和带边缘延展的参考 UV 图。源文件无需作为游戏资源提交。先重新打包主场景并重建小熊底图，再运行：

```sh
blender -b fitted-cat.blend --python art/export_cat.py
PURRLOCK_CAT_STAGE=/tmp/purrlock-bake blender -b art/room.blend --python art/clear_room_cat.py
python3 art/pack_cat_room.py /tmp/purrlock-bake/sofa-clear.png cat-reference-uv.png
```

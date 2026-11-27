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

质量是供以后给刚体设定质量的参考值，存在 Blender 集合的 `mass_kg` 中，缩放实例时应重新评估。第一关仍然仅收集餐具：花盆、篮子和家具固定；枝叶随点击摆动，拖鞋轻晃，气球在绳端附近回摆。交互反馈是受控制的动画，不代表这些装饰物已启用完整的刚体或布料模拟。气球、木块和玩具车仍使用带有独立乳胶、橡胶和漆面材质的 3D 模型。

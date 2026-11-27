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

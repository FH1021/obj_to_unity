# obj_to_unity
向unity中导入obj文件的外部用用程序
核心导入逻辑
选择 OBJ：通过 filedialog 多选 .obj 文件
定位依赖：
逐行读取 OBJ 文件，解析 mtllib 行，找到引用的 .mtl 材质文件
再逐行读取 MTL 文件，解析 map_Kd / map_Ks / bump 等行，找到引用的贴图文件（.png/.jpg/.tga 等）
复制到 Unity：用 shutil.copy2 把 OBJ、MTL、贴图一并复制到 Assets/<目标子文件夹> 下
触发导入：Unity Editor 启动时会自动扫描 Assets 目录变化，新放入的 OBJ 会被自动识别并导入为模型资源 ——这一步不需要外部程序调用 Unity API

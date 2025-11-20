import os
from typing import Set, List, Optional


def collect_fifth_column_unique_values(
        root_dir: str,
        skip_header: bool = False,
        encoding: str = 'utf-8',
        delimiter: Optional[str] = None
) -> Set[str]:
    """
    递归遍历根目录下所有txt文件，收集第五列的所有唯一值

    参数:
        root_dir: 根目录路径（要搜索的文件夹起点）
        skip_header: 是否跳过文件第一行（如果第一行是表头）
        encoding: 文件编码格式（默认utf-8，常见还有gbk）
        delimiter: 列分隔符（None表示自动处理空格/制表符，可指定如','、'\t'等）

    返回:
        所有第五列的唯一值集合
    """
    unique_values = set()

    # 递归遍历所有文件夹和文件
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            # 只处理txt文件
            if file.lower().endswith('.txt'):
                file_path = os.path.join(root, file)
                print(f"正在处理文件: {file_path}")

                try:
                    # 打开文件并读取内容
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        lines = f.readlines()

                    # 跳过表头（如果需要）
                    if skip_header and lines:
                        lines = lines[1:]

                    # 处理每一行
                    for line_num, line in enumerate(lines, start=1):
                        # 去除行首尾空白字符（换行符、空格等）
                        line = line.strip()
                        if not line:  # 跳过空行
                            continue

                        # 分割列（根据指定分隔符或自动分割）
                        if delimiter is None:
                            # 自动处理多个空格/制表符作为分隔符
                            columns = line.split()
                        else:
                            # 使用指定分隔符分割
                            columns = line.split(delimiter)

                        # 检查是否有第五列（索引为4，因为Python从0开始计数）
                        if len(columns) >= 5:
                            fifth_col = columns[4].strip()
                            if fifth_col:  # 不收集空值
                                unique_values.add(fifth_col)
                        else:
                            # 输出警告：该行列数不足
                            print(f"  警告: {file_path} 第{line_num}行列数不足5列，跳过该行")

                except Exception as e:
                    # 处理文件读取错误
                    print(f"  错误: 无法读取 {file_path} - {str(e)}")

    return unique_values


def main():
    # -------------------------- 配置项 --------------------------
    ROOT_DIRECTORY = r"data"  # 替换为你的根目录路径
    SKIP_HEADER = False  # 如果文件第一行是表头，改为True
    FILE_ENCODING = "utf-8"  # 中文文件可能需要改为"gbk"或"gb2312"
    COLUMN_DELIMITER = None  # 分隔符（None=自动处理空格/制表符，可指定如',' '\t'等）
    OUTPUT_FILE = "data/第五列唯一值.txt"  # 结果保存文件名
    # -------------------------------------------------------------

    # 检查根目录是否存在
    if not os.path.exists(ROOT_DIRECTORY):
        print(f"错误：根目录 {ROOT_DIRECTORY} 不存在！")
        return

    print(f"开始搜索 {ROOT_DIRECTORY} 下所有txt文件的第五列唯一值...")
    print(f"是否跳过表头: {'是' if SKIP_HEADER else '否'}")
    print(f"文件编码: {FILE_ENCODING}")
    print(f"列分隔符: {'自动识别' if COLUMN_DELIMITER is None else COLUMN_DELIMITER}")
    print("-" * 50)

    # 收集唯一值
    unique_values = collect_fifth_column_unique_values(
        root_dir=ROOT_DIRECTORY,
        skip_header=SKIP_HEADER,
        encoding=FILE_ENCODING,
        delimiter=COLUMN_DELIMITER
    )

    # 输出结果
    print("\n" + "-" * 50)
    print(f"搜索完成！共找到 {len(unique_values)} 个不同的值：")
    print("-" * 50)

    # 排序后打印（可选）
    sorted_values = sorted(unique_values)
    for idx, value in enumerate(sorted_values, start=1):
        print(f"{idx:3d}. {value}")

    # 保存结果到文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"搜索目录: {ROOT_DIRECTORY}\n")
        f.write(f"是否跳过表头: {'是' if SKIP_HEADER else '否'}\n")
        f.write(f"文件编码: {FILE_ENCODING}\n")
        f.write(f"列分隔符: {'自动识别' if COLUMN_DELIMITER is None else COLUMN_DELIMITER}\n")
        f.write(f"总唯一值数量: {len(unique_values)}\n")
        f.write("-" * 50 + "\n")
        for value in sorted_values:
            f.write(value + "\n")

    print(f"\n结果已保存到: {os.path.abspath(OUTPUT_FILE)}")


if __name__ == "__main__":
    main()
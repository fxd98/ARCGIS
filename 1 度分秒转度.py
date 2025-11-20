import csv
import re
import os
from typing import Optional


def dms_to_dd(dms_str: str, data_type: str = 'lon') -> Optional[float]:
    """
    度分秒（DMS）转十进制度（DD）核心函数
    支持格式：
    - 无方向：110°33'44.164"、110° 33' 44.164（秒后可无引号）
    - 中文方向：东经110°33'44.164"、110°33'44.164"西经
    - 字母方向：110°33'44.164"E、30°15'22.3"S
    参数：
        dms_str: 度分秒格式字符串
        data_type: 'lon'=经度（范围-180~180），'lat'=纬度（范围-90~90）
    返回：
        十进制度数值（失败返回None）
    """
    # 处理空值/NaN
    if not dms_str or str(dms_str).strip() in ['', 'nan', 'NaN']:
        print(f"⚠️  空值/无效值，跳过转换")
        return None

    dms_str = str(dms_str).strip()
    direction = 1  # 默认东经/北纬（正值）

    # 1. 识别方向词（中文/字母）
    # 中文方向词（前缀/后缀）
    chinese_dir = re.search(r'^(东经|西经|北纬|南纬)\s*|\s*(东经|西经|北纬|南纬)$', dms_str)
    if chinese_dir:
        dir_word = chinese_dir.group(1) or chinese_dir.group(2)
        direction = -1 if dir_word in ['西经', '南纬'] else 1
        dms_str = re.sub(r'^(东经|西经|北纬|南纬)\s*|\s*(东经|西经|北纬|南纬)$', '', dms_str).strip()
    # 字母方向词（后缀）
    elif dms_str[-1].upper() in ['N', 'S', 'E', 'W']:
        dir_char = dms_str[-1].upper()
        direction = -1 if dir_char in ['S', 'W'] else 1
        dms_str = dms_str[:-1].strip()

    # 2. 匹配度分秒核心结构（兼容符号、空格差异）
    # 正则支持：°/′/'、″/"、空格/无空格、带/不带小数
    pattern = r'''(\d+(?:\.\d+)?)[°](\d+(?:\.\d+)?)[′'](\d+(?:\.\d+)?)[″"]?'''
    match = re.fullmatch(pattern, dms_str.replace(' ', ''))  # 去除空格统一匹配

    if not match:
        # 兼容横杠/空格分隔（如110-33-44.164、110 33 44.164）
        pattern_backup = r'(\d+(?:\.\d+)?)[\s\-](\d+(?:\.\d+)?)[\s\-](\d+(?:\.\d+)?)'
        match = re.fullmatch(pattern_backup, dms_str.replace('°', ' ').replace("'", ' ').replace('"', ' ').strip())

    if not match:
        print(f"❌ 无法解析格式：{dms_str}（需符合度分秒标准，如110°33'44.164\"）")
        return None

    # 3. 提取并验证度、分、秒
    try:
        deg = float(match.group(1))
        min_ = float(match.group(2))
        sec = float(match.group(3))
    except Exception as e:
        print(f"❌ 数值转换失败：{dms_str} - {str(e)}")
        return None

    # 基础验证（分秒<60，经纬度范围）
    if min_ >= 60 or sec >= 60:
        print(f"❌ 分/秒超出范围（需<60）：{dms_str}（分：{min_}，秒：{sec}）")
        return None
    if data_type == 'lon' and deg > 180:
        print(f"❌ 经度超出范围（需≤180）：{dms_str}（度：{deg}）")
        return None
    if data_type == 'lat' and deg > 90:
        print(f"❌ 纬度超出范围（需≤90）：{dms_str}（度：{deg}）")
        return None

    # 4. 计算十进制度（保留6位小数，满足GIS需求）
    dd = (deg + min_ / 60 + sec / 3600) * direction
    return round(dd, 6)


def convert_csv_dms(
        input_csv: str,
        output_csv: str,
        lon_col: str or int = "经度",
        lat_col: str or int = "纬度",
        encoding: str = "utf-8",
        delimiter: str = ","
) -> None:
    """
    CSV经纬度批量转换主函数
    参数：
        input_csv: 输入CSV文件路径
        output_csv: 输出CSV文件路径（新增转换列，保留原始数据）
        lon_col: 经度列名（字符串）或列索引（整数，从0开始）
        lat_col: 纬度列名（字符串）或列索引（整数，从0开始）
        encoding: 文件编码（中文文件建议用"gbk"）
        delimiter: CSV分隔符（逗号用","，制表符用"\t"）
    """
    # 检查输入文件是否存在
    if not os.path.exists(input_csv):
        print(f"❌ 错误：输入文件 {input_csv} 不存在！")
        return

    # 统计变量
    total_rows = 0
    success_rows = 0
    fail_rows = []

    try:
        with open(input_csv, "r", encoding=encoding, newline="") as infile, \
                open(output_csv, "w", encoding=encoding, newline="") as outfile:

            reader = csv.reader(infile, delimiter=delimiter)
            writer = csv.writer(outfile, delimiter=delimiter)

            # 处理表头：确定经纬度列索引
            header = next(reader)
            try:
                # 按列名或索引定位
                lon_idx = lon_col if isinstance(lon_col, int) else header.index(lon_col)
                lat_idx = lat_col if isinstance(lat_col, int) else header.index(lat_col)
            except ValueError:
                print(f"❌ 错误：未找到经纬度列！可用列名：{header}")
                return
            except IndexError:
                print(f"❌ 错误：经纬度列索引超出范围（表头共 {len(header)} 列）")
                return

            # 写入新表头（新增转换列）
            new_header = header + ["经度_十进制度", "纬度_十进制度"]
            writer.writerow(new_header)
            print(f"✅ 表头处理完成，新增列：经度_十进制度、纬度_十进制度")

            # 批量转换数据行
            for row_num, row in enumerate(reader, start=2):  # 行号从2开始（跳过表头）
                total_rows += 1
                new_row = row.copy()

                # 转换经度
                lon_dms = row[lon_idx].strip() if (lon_idx < len(row)) else ""
                lon_dd = dms_to_dd(lon_dms, data_type="lon")

                # 转换纬度
                lat_dms = row[lat_idx].strip() if (lat_idx < len(row)) else ""
                lat_dd = dms_to_dd(lat_dms, data_type="lat")

                # 追加转换结果
                new_row.append(str(lon_dd) if lon_dd is not None else "转换失败")
                new_row.append(str(lat_dd) if lat_dd is not None else "转换失败")

                # 统计成功/失败
                if lon_dd is not None and lat_dd is not None:
                    success_rows += 1
                else:
                    fail_rows.append((row_num, lon_dms, lat_dms))

                # 写入行数据
                writer.writerow(new_row)

        # 输出转换统计
        print("\n" + "=" * 50)
        print(f"📊 转换完成！")
        print(f"输入文件：{input_csv}")
        print(f"输出文件：{output_csv}")
        print(f"总数据行：{total_rows}")
        print(f"成功转换：{success_rows} 行")
        print(f"转换失败：{len(fail_rows)} 行")

        # 显示失败行（前5个）
        if fail_rows:
            print("\n❌ 失败行示例（行号、经度、纬度）：")
            for rn, lon, lat in fail_rows[:5]:
                print(f"行{rn}：经度='{lon}' | 纬度='{lat}'")
            if len(fail_rows) > 5:
                print(f"... 还有 {len(fail_rows) - 5} 行转换失败")

    except Exception as e:
        print(f"❌ 转换异常：{str(e)}")


def main():
    # -------------------------- 请修改以下配置 --------------------------
    INPUT_CSV = r"data/遥感解译出灾害点.csv"  # 输入CSV路径（例：r"D:\data\原始数据.csv"）
    OUTPUT_CSV = r"data/转换后数据.csv"  # 输出CSV路径（例：r"D:\data\转换后数据.csv"）
    LONGITUDE_COL = "经度"  # 经度列名（如列索引是0，可改为 0）
    LATITUDE_COL = "纬度"  # 纬度列名（如列索引是1，可改为 1）
    FILE_ENCODING = "utf-8"  # 中文文件改为 "gbk"（解决乱码）
    CSV_DELIMITER = ","  # 分隔符：逗号用","，制表符用"\t"
    # -------------------------------------------------------------------

    # 执行转换
    print("🚀 开始经纬度转换（度分秒→十进制度）")
    print(f"经度列：{LONGITUDE_COL} | 纬度列：{LATITUDE_COL}")
    print(f"编码：{FILE_ENCODING} | 分隔符：{CSV_DELIMITER}")
    print("=" * 50)

    convert_csv_dms(
        input_csv=INPUT_CSV,
        output_csv=OUTPUT_CSV,
        lon_col=LONGITUDE_COL,
        lat_col=LATITUDE_COL,
        encoding=FILE_ENCODING,
        delimiter=CSV_DELIMITER
    )


if __name__ == "__main__":
    main()
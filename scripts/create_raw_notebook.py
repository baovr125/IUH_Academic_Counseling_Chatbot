import os
import glob
import json
import re

os.makedirs('scripts', exist_ok=True)

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Khảo sát dữ liệu thô để tìm \"Điểm G\" cho Chunk Size\n",
    "Notebook này quét qua toàn bộ các file Markdown thu thập được, phân tách chúng thành các đoạn văn (Paragraphs) và tính toán độ dài tự nhiên của chúng. Mục đích là để tìm ra con số `max_child_size` tối ưu nhất dựa trên toán học và thống kê, thay vì đoán mò."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "import glob\n",
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "import numpy as np\n",
    "\n",
    "sns.set_theme(style=\"whitegrid\")\n",
    "plt.rcParams['figure.figsize'] = (12, 6)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 1. Đọc toàn bộ dữ liệu thô (Raw Crawled Markdown)\n",
    "md_files = glob.glob('../data/crawled_markdown/*.md')\n",
    "print(f\"Tìm thấy {len(md_files)} files markdown.\")\n",
    "\n",
    "all_paragraphs = []\n",
    "for file in md_files:\n",
    "    with open(file, 'r', encoding='utf-8') as f:\n",
    "        content = f.read()\n",
    "        # Loại bỏ phần YAML Frontmatter\n",
    "        import re\n",
    "        content = re.sub(r'^---\\n.*?\\n---\\n+', '', content, flags=re.DOTALL)\n",
    "        \n",
    "        # Tách thành các khối văn bản tự nhiên (cách nhau bởi 1 dòng trắng)\n",
    "        paragraphs = content.split('\\n\\n')\n",
    "        for p in paragraphs:\n",
    "            p = p.strip()\n",
    "            if p:\n",
    "                all_paragraphs.append(p)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 2. Tính toán độ dài của từng đoạn văn\n",
    "df = pd.DataFrame({'paragraph': all_paragraphs})\n",
    "df['char_length'] = df['paragraph'].apply(len)\n",
    "df['word_count'] = df['paragraph'].apply(lambda x: len(x.split()))\n",
    "\n",
    "print(\"===== THỐNG KÊ ĐỘ DÀI ĐOẠN VĂN TỰ NHIÊN =====\")\n",
    "print(f\"Tổng số đoạn văn: {len(df):,}\")\n",
    "print(f\"Độ dài trung bình: {df['char_length'].mean():.0f} ký tự\")\n",
    "print(f\"Đoạn văn dài nhất: {df['char_length'].max():,} ký tự\")\n",
    "print(\"\\n--- Tỷ lệ bao phủ (Percentiles) ---\")\n",
    "for p in [50, 75, 90, 95, 99]:\n",
    "    val = np.percentile(df['char_length'], p)\n",
    "    print(f\"{p}% đoạn văn có độ dài DƯỚI: {val:.0f} ký tự\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 3. Vẽ biểu đồ phân phối\n",
    "# Loại bỏ các đoạn văn quá dài (Outliers > 2000) để biểu đồ dễ nhìn hơn\n",
    "filtered_df = df[df['char_length'] <= 2000]\n",
    "\n",
    "plt.figure(figsize=(12, 6))\n",
    "sns.histplot(filtered_df['char_length'], bins=50, kde=True, color='purple')\n",
    "\n",
    "# Vẽ các đường Percentile\n",
    "p90 = np.percentile(df['char_length'], 90)\n",
    "p95 = np.percentile(df['char_length'], 95)\n",
    "plt.axvline(p90, color='r', linestyle='--', label=f'90th Percentile ({p90:.0f} chars)')\n",
    "plt.axvline(p95, color='orange', linestyle='--', label=f'95th Percentile ({p95:.0f} chars)')\n",
    "\n",
    "plt.title('Phân phối độ dài Tự Nhiên của các Đoạn văn trong Dữ liệu IUH')\n",
    "plt.xlabel('Số ký tự trong 1 đoạn văn')\n",
    "plt.ylabel('Số lượng đoạn văn')\n",
    "plt.legend()\n",
    "plt.show()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.10"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

with open('scripts/visualize_raw_data.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)
print("Created scripts/visualize_raw_data.ipynb successfully!")

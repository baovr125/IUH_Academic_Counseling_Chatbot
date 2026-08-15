import json
import os

os.makedirs('scripts', exist_ok=True)

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Thống Kê và Trực Quan Hóa Dữ Liệu Chunks (RAG Pipeline)\n",
    "Notebook này phân tích các file `parents.json` và `children.json` để đánh giá chất lượng của phương pháp Hybrid Hierarchical Chunking."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import json\n",
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "\n",
    "# Thiết lập giao diện biểu đồ\n",
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
    "# 1. Đọc dữ liệu\n",
    "with open('../data/parents.json', 'r', encoding='utf-8') as f:\n",
    "    parents = json.load(f)\n",
    "with open('../data/children.json', 'r', encoding='utf-8') as f:\n",
    "    children = json.load(f)\n",
    "\n",
    "# 2. Chuyển đổi thành DataFrame\n",
    "df_parents = pd.DataFrame(parents)\n",
    "df_children = pd.DataFrame(children)\n",
    "\n",
    "# Tính toán độ dài ký tự\n",
    "df_parents['char_length'] = df_parents['text'].apply(len)\n",
    "df_children['char_length'] = df_children['text'].apply(len)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 3. Thống kê tổng quan\n",
    "print(\"===== THỐNG KÊ TỔNG QUAN =====\")\n",
    "print(f\"Tổng số Parent Chunks: {len(df_parents):,}\")\n",
    "print(f\"Tổng số Child Chunks: {len(df_children):,}\")\n",
    "print(f\"Tỷ lệ nở (Child/Parent): {len(df_children)/len(df_parents):.2f} children/parent\")\n",
    "print(f\"Độ dài trung bình Parent: {df_parents['char_length'].mean():.0f} ký tự\")\n",
    "print(f\"Độ dài trung bình Child: {df_children['char_length'].mean():.0f} ký tự\")\n",
    "print(f\"Độ dài lớn nhất Child: {df_children['char_length'].max()} ký tự\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 4. Phân phối độ dài của Child Chunks\n",
    "plt.figure(figsize=(10, 5))\n",
    "sns.histplot(df_children['char_length'], bins=50, kde=True, color='blue')\n",
    "plt.title('Phân phối độ dài (số ký tự) của Child Chunks\\n(Giúp đánh giá xem chunk có bị vượt giới hạn Token của Embedding Model không)')\n",
    "plt.xlabel('Số ký tự')\n",
    "plt.ylabel('Số lượng Chunks')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 5. Phân phối độ dài của Parent Chunks (Loại bỏ các Outlier khổng lồ để dễ nhìn)\n",
    "plt.figure(figsize=(10, 5))\n",
    "filtered_parents = df_parents[df_parents['char_length'] <= 5000]\n",
    "sns.histplot(filtered_parents['char_length'], bins=50, kde=True, color='green')\n",
    "plt.title('Phân phối độ dài của Parent Chunks (Zoom vào < 5000 ký tự)\\n(Các chunk lớn hơn 5000 ký tự đã bị ẩn khỏi biểu đồ này)')\n",
    "plt.xlabel('Số ký tự')\n",
    "plt.ylabel('Số lượng Chunks')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 6. Tần suất chia nhỏ (Bao nhiêu Child được đẻ ra từ 1 Parent)\n",
    "child_counts = df_children['parent_id'].value_counts()\n",
    "\n",
    "plt.figure(figsize=(10, 5))\n",
    "sns.histplot(child_counts, bins=range(1, child_counts.max() + 2), kde=False, color='orange')\n",
    "plt.title('Số lượng Child Chunks sinh ra từ một Parent Chunk')\n",
    "plt.xlabel('Số lượng Child')\n",
    "plt.ylabel('Số lượng Parent')\n",
    "plt.xlim(1, child_counts.max() + 1)\n",
    "plt.show()\n",
    "\n",
    "print(f\"Nhiều nhất một Parent bị cắt thành {child_counts.max()} Children.\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 7. Thống kê theo từng tài liệu nguồn (Source URL)\n",
    "df_children['source_url'] = df_children['metadata'].apply(lambda x: x.get('source_url', 'Unknown'))\n",
    "source_counts = df_children['source_url'].value_counts().head(10)\n",
    "\n",
    "plt.figure(figsize=(12, 6))\n",
    "sns.barplot(x=source_counts.values, y=source_counts.index, palette='viridis')\n",
    "plt.title('Top 10 Tài liệu nguồn sinh ra nhiều Child Chunks nhất')\n",
    "plt.xlabel('Số lượng Child Chunks')\n",
    "plt.ylabel('URL Tài liệu')\n",
    "plt.tight_layout()\n",
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

with open('scripts/visualize_chunks.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)
print("Created scripts/visualize_chunks.ipynb successfully!")

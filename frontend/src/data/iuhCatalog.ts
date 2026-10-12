/**
 * Danh mục Khoa / Viện và Ngành đào tạo đại học của Trường ĐH Công nghiệp TP.HCM (IUH).
 *
 * Nguồn: danh sách đơn vị lấy từ https://iuh.edu.vn/vi/so-do-bo-may-to-chuc.html (15 khoa + 4 viện);
 * ngành tổng hợp từ trang từng khoa/viện và thông tin tuyển sinh 2025. Các mục có ghi chú
 * "CẦN XÁC NHẬN" chưa được đối chiếu với Phòng Đào tạo — danh mục thay đổi theo từng năm tuyển sinh,
 * nên giao diện luôn có mục "Khác…" cho phép nhập tay; server không bắt buộc giá trị thuộc danh mục.
 */
export interface IuhUnit {
  id: string;
  name: string;
  kind: "khoa" | "vien";
  majors: string[];
}

/** Giá trị đặc biệt của mục "Khác…" trong dropdown (không bao giờ gửi lên server). */
export const OTHER = "__other__";

export const IUH_UNITS: IuhUnit[] = [
  {
    id: "cntt",
    name: "Khoa Công nghệ Thông tin",
    kind: "khoa",
    majors: [
      "Khoa học máy tính",
      "Kỹ thuật phần mềm",
      "Công nghệ thông tin",
      "Hệ thống thông tin",
      "Trí tuệ nhân tạo", // CẦN XÁC NHẬN (chuyên ngành mới 2025)
    ],
  },
  {
    id: "co-khi",
    name: "Khoa Công nghệ Cơ khí",
    kind: "khoa",
    majors: ["Công nghệ kỹ thuật cơ khí", "Công nghệ chế tạo máy", "Công nghệ kỹ thuật cơ điện tử"],
  },
  {
    id: "dien",
    name: "Khoa Công nghệ Điện",
    kind: "khoa",
    majors: [
      "Kỹ thuật điện",
      "Điều khiển và tự động hóa", // CẦN XÁC NHẬN tên chính thức
      "Điện hạt nhân", // CẦN XÁC NHẬN (chuyên ngành mới 2025)
    ],
  },
  {
    id: "dien-tu",
    name: "Khoa Công nghệ Điện tử",
    kind: "khoa",
    majors: [
      "Công nghệ kỹ thuật điện tử - viễn thông",
      "Công nghệ kỹ thuật máy tính",
      "IoT và trí tuệ nhân tạo ứng dụng",
    ],
  },
  { id: "dong-luc", name: "Khoa Công nghệ Động lực", kind: "khoa", majors: ["Công nghệ kỹ thuật ô tô"] },
  {
    id: "nhiet-lanh",
    name: "Khoa Công nghệ Nhiệt - Lạnh",
    kind: "khoa",
    majors: [
      "Công nghệ kỹ thuật nhiệt",
      "Công nghệ kỹ thuật năng lượng", // CẦN XÁC NHẬN
      "Quản lý năng lượng",
    ],
  },
  { id: "may-thoi-trang", name: "Khoa Công nghệ May - Thời trang", kind: "khoa", majors: ["Công nghệ may", "Thiết kế thời trang"] },
  {
    id: "hoa-hoc",
    name: "Khoa Công nghệ Hóa học",
    kind: "khoa",
    majors: [
      "Công nghệ kỹ thuật hóa học",
      "Công nghệ hữu cơ",
      "Công nghệ vô cơ - vật liệu",
      "Công nghệ hóa dầu",
      "Kỹ thuật hóa phân tích",
    ],
  },
  { id: "khcb", name: "Khoa Khoa học Cơ bản", kind: "khoa", majors: [] }, // không có ngành đại học riêng
  {
    id: "luat-khct",
    name: "Khoa Luật và Khoa học chính trị",
    kind: "khoa",
    majors: ["Luật kinh tế", "Luật quốc tế"], // CẦN XÁC NHẬN
  },
  { id: "ngoai-ngu", name: "Khoa Ngoại ngữ", kind: "khoa", majors: ["Ngôn ngữ Anh", "Ngôn ngữ Trung Quốc"] },
  {
    id: "qtkd",
    name: "Khoa Quản trị Kinh doanh",
    kind: "khoa",
    majors: ["Quản trị kinh doanh", "Quản trị nhân lực", "Quản trị cung ứng và logistics", "Marketing"],
  },
  {
    id: "thuong-mai-du-lich",
    name: "Khoa Thương mại - Du lịch",
    kind: "khoa",
    majors: [
      "Kinh doanh quốc tế",
      "Thương mại điện tử",
      "Quản trị dịch vụ du lịch và lữ hành",
      "Quản trị khách sạn",
      "Quản trị nhà hàng và dịch vụ ăn uống",
    ],
  },
  {
    id: "xay-dung",
    name: "Khoa Kỹ thuật Xây dựng",
    kind: "khoa",
    majors: ["Kỹ thuật xây dựng", "Kỹ thuật xây dựng công trình giao thông"],
  },
  { id: "suc-khoe", name: "Khoa Khoa học Sức khỏe", kind: "khoa", majors: ["Dược học"] }, // CẦN XÁC NHẬN
  {
    id: "tai-chinh-ke-toan",
    name: "Viện Tài chính - Kế toán",
    kind: "vien",
    majors: ["Kế toán", "Kiểm toán", "Tài chính - Ngân hàng", "Công nghệ tài chính"],
  },
  {
    id: "sinh-hoc-thuc-pham",
    name: "Viện Công nghệ Sinh học và Thực phẩm",
    kind: "vien",
    majors: [
      "Công nghệ thực phẩm",
      "Công nghệ sinh học",
      "Đảm bảo chất lượng và an toàn thực phẩm",
      "Dinh dưỡng và khoa học thực phẩm",
    ],
  },
  {
    id: "moi-truong",
    name: "Viện Khoa học Công nghệ và Quản lý Môi trường",
    kind: "vien",
    majors: [
      "Công nghệ kỹ thuật môi trường",
      "Quản lý tài nguyên và môi trường",
      "Khoa học môi trường", // CẦN XÁC NHẬN
    ],
  },
  { id: "quoc-te-sdh", name: "Viện Đào tạo Quốc tế và Sau đại học", kind: "vien", majors: [] }, // liên kết quốc tế / sau đại học
];

/** Chuẩn hóa để tìm kiếm: bỏ dấu tiếng Việt, đ→d, chữ thường, gom khoảng trắng. */
export function searchNormalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/gi, "d")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

export function findUnit(name: string): IuhUnit | undefined {
  const target = searchNormalize(name);
  return IUH_UNITS.find((u) => searchNormalize(u.name) === target);
}

/** Một ngành (chuỗi) có thuộc danh mục của khoa/viện này không (so khớp không phân biệt dấu/hoa thường). */
export function unitHasMajor(unit: IuhUnit | undefined, major: string): boolean {
  if (!unit) return false;
  const target = searchNormalize(major);
  return unit.majors.some((m) => searchNormalize(m) === target);
}

/** Tên ngành chuẩn trong danh mục của khoa/viện (so khớp không dấu/hoa thường); undefined nếu không có. */
export function findMajor(unit: IuhUnit | undefined, major: string): string | undefined {
  if (!unit) return undefined;
  const target = searchNormalize(major);
  return unit.majors.find((m) => searchNormalize(m) === target);
}

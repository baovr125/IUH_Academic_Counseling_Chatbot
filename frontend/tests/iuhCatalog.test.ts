import { renderHook, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { IUH_UNITS, OTHER, findMajor, findUnit, searchNormalize } from "../src/data/iuhCatalog";
import { resolveSelection, useCatalogSelection } from "../src/hooks/useCatalogSelection";

describe("danh mục IUH", () => {
  it("19 đơn vị (15 khoa + 4 viện), id và tên duy nhất, không rỗng", () => {
    expect(IUH_UNITS).toHaveLength(19);
    expect(IUH_UNITS.filter((u) => u.kind === "khoa")).toHaveLength(15);
    expect(IUH_UNITS.filter((u) => u.kind === "vien")).toHaveLength(4);
    expect(new Set(IUH_UNITS.map((u) => u.id)).size).toBe(IUH_UNITS.length);
    expect(new Set(IUH_UNITS.map((u) => searchNormalize(u.name))).size).toBe(IUH_UNITS.length);
    for (const u of IUH_UNITS) {
      expect(u.name.trim()).toBe(u.name);
      expect(u.name.length).toBeGreaterThanOrEqual(2);
      expect(new Set(u.majors.map(searchNormalize)).size).toBe(u.majors.length); // không trùng trong một khoa
      for (const m of u.majors) {
        expect(m.trim()).toBe(m);
        expect(m.length).toBeGreaterThanOrEqual(2);
        expect(m.length).toBeLessThanOrEqual(150); // giới hạn của server
      }
    }
  });

  it("không có tên nào trùng với giá trị đặc biệt OTHER", () => {
    expect(IUH_UNITS.some((u) => u.name === OTHER || u.majors.includes(OTHER))).toBe(false);
  });

  it("searchNormalize bỏ dấu tiếng Việt, đ → d, hạ chữ thường", () => {
    expect(searchNormalize("  Công  nghệ Điện Tử ")).toBe("cong nghe dien tu");
    expect(searchNormalize("ĐÀO TẠO")).toBe("dao tao");
  });

  it("findUnit / findMajor so khớp không dấu và trả tên chuẩn", () => {
    const unit = findUnit("khoa cong nghe thong tin");
    expect(unit?.name).toBe("Khoa Công nghệ Thông tin");
    expect(findMajor(unit, "ky thuat phan mem")).toBe("Kỹ thuật phần mềm");
    expect(findMajor(unit, "Kế toán")).toBeUndefined();
    expect(findUnit("Khoa không tồn tại")).toBeUndefined();
  });
});

describe("resolveSelection", () => {
  it("giá trị trong danh mục được chọn đúng mục", () => {
    expect(resolveSelection("Khoa Ngoại ngữ", "Ngôn ngữ Anh")).toEqual({
      departmentSel: "Khoa Ngoại ngữ",
      departmentOther: "",
      majorSel: "Ngôn ngữ Anh",
      majorOther: "",
    });
  });

  it('giá trị cũ ngoài danh mục rơi vào "Khác…" và giữ nguyên văn bản (không mất dữ liệu)', () => {
    expect(resolveSelection("Khoa cũ đã đổi tên", "Ngành cũ")).toEqual({
      departmentSel: OTHER,
      departmentOther: "Khoa cũ đã đổi tên",
      majorSel: OTHER,
      majorOther: "Ngành cũ",
    });
    const mixed = resolveSelection("Khoa Ngoại ngữ", "Ngành không còn");
    expect(mixed.departmentSel).toBe("Khoa Ngoại ngữ");
    expect(mixed.majorSel).toBe(OTHER);
    expect(mixed.majorOther).toBe("Ngành không còn");
  });

  it("rỗng thì không chọn gì", () => {
    expect(resolveSelection("", "")).toEqual({ departmentSel: "", departmentOther: "", majorSel: "", majorOther: "" });
  });
});

describe("useCatalogSelection", () => {
  it("đổi khoa thì xóa ngành; khoa không có ngành đại học tự chọn 'Khác…' cho ngành", () => {
    const { result } = renderHook(() => useCatalogSelection());
    act(() => result.current.chooseDepartment("Khoa Công nghệ Thông tin"));
    expect(result.current.majorOptions).toContain("Kỹ thuật phần mềm");
    act(() => result.current.chooseMajor("Kỹ thuật phần mềm"));
    expect(result.current.major).toBe("Kỹ thuật phần mềm");

    act(() => result.current.chooseDepartment("Khoa Ngoại ngữ"));
    expect(result.current.majorSel).toBe("");
    expect(result.current.major).toBe("");

    act(() => result.current.chooseDepartment("Khoa Khoa học Cơ bản")); // không có ngành
    expect(result.current.majorSel).toBe(OTHER);
    act(() => result.current.setMajorOther("  Toán ứng dụng "));
    expect(result.current.major).toBe("Toán ứng dụng");
  });

  it("department/major là giá trị gửi lên server (tên trong danh mục hoặc chuỗi nhập tay đã trim)", () => {
    const { result } = renderHook(() => useCatalogSelection());
    act(() => result.current.chooseDepartment(OTHER));
    act(() => result.current.setDepartmentOther("  Khoa mới  "));
    expect(result.current.department).toBe("Khoa mới");
    expect(result.current.departmentSel).toBe(OTHER);
  });

  it("reset nạp lại từ dữ liệu hồ sơ", () => {
    const { result } = renderHook(() => useCatalogSelection());
    act(() => result.current.reset("Viện Tài chính - Kế toán", "Kế toán"));
    expect(result.current.department).toBe("Viện Tài chính - Kế toán");
    expect(result.current.major).toBe("Kế toán");
  });
});

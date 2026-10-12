import { useCallback, useMemo, useState } from "react";
import { OTHER, findMajor, findUnit } from "../data/iuhCatalog";

interface Selection {
  departmentSel: string;
  departmentOther: string;
  majorSel: string;
  majorOther: string;
}

/** Chuyển giá trị đã lưu (chuỗi tự do) thành lựa chọn trong dropdown; giá trị ngoài danh mục rơi vào "Khác…". */
export function resolveSelection(department = "", major = ""): Selection {
  const dep = department.trim();
  const maj = major.trim();
  const unit = findUnit(dep);
  const departmentSel = unit ? unit.name : dep ? OTHER : "";
  const departmentOther = unit || !dep ? "" : dep;

  let majorSel = "";
  let majorOther = "";
  if (maj) {
    const known = findMajor(unit, maj);
    if (known) majorSel = known;
    else {
      majorSel = OTHER;
      majorOther = maj;
    }
  } else if (departmentSel && (!unit || unit.majors.length === 0)) {
    majorSel = OTHER; // khoa không có ngành trong danh mục: chỉ còn nhập tay
  }
  return { departmentSel, departmentOther, majorSel, majorOther };
}

/**
 * Trạng thái của cặp dropdown Khoa/Viện → Ngành (ngành lọc theo khoa), dùng chung cho đăng ký và hồ sơ.
 * `department`/`major` là giá trị thật cần gửi lên server (tên trong danh mục hoặc chuỗi nhập tay).
 */
export function useCatalogSelection(initialDepartment = "", initialMajor = "") {
  const [sel, setSel] = useState<Selection>(() => resolveSelection(initialDepartment, initialMajor));

  const unit = findUnit(sel.departmentSel);
  const majorOptions = useMemo(() => unit?.majors ?? [], [unit]);
  const department = (sel.departmentSel === OTHER ? sel.departmentOther : sel.departmentSel).trim();
  const major = (sel.majorSel === OTHER ? sel.majorOther : sel.majorSel).trim();

  const chooseDepartment = useCallback((value: string) => {
    // Đổi khoa thì ngành cũ không còn hợp lệ. Khoa không có ngành trong danh mục ("Khác…" hoặc khoa không có
    // ngành đại học) chỉ còn lựa chọn nhập tay nên chọn sẵn "Khác…" cho ngành.
    const next = findUnit(value);
    const onlyOther = value !== "" && (value === OTHER || !next || next.majors.length === 0);
    setSel({
      departmentSel: value,
      departmentOther: "",
      majorSel: onlyOther ? OTHER : "",
      majorOther: "",
    });
  }, []);

  const chooseMajor = useCallback((value: string) => {
    setSel((prev) => ({ ...prev, majorSel: value, majorOther: "" }));
  }, []);

  const setDepartmentOther = useCallback((value: string) => setSel((prev) => ({ ...prev, departmentOther: value })), []);
  const setMajorOther = useCallback((value: string) => setSel((prev) => ({ ...prev, majorOther: value })), []);
  const reset = useCallback((dep?: string | null, maj?: string | null) => setSel(resolveSelection(dep ?? "", maj ?? "")), []);

  return {
    ...sel,
    department,
    major,
    majorOptions,
    chooseDepartment,
    chooseMajor,
    setDepartmentOther,
    setMajorOther,
    reset,
  };
}

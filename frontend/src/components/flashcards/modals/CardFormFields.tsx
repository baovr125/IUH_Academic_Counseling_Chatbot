import React from "react";
import { FcInput, FcSelect } from "../ui";

export interface CardFormValues {
  term: string;
  definition: string;
  phonetic: string;
  example: string;
  partOfSpeech: string;
}

interface CardFormFieldsProps {
  values: CardFormValues;
  onChange: (patch: Partial<CardFormValues>) => void;
  /** Mã ngôn ngữ của từ, để đọc đúng giọng/chính tả bằng trình đọc màn hình. */
  lang?: string;
  /** Placeholder gợi ý (chỉ dùng khi thêm mới). */
  showExamples?: boolean;
}

/** Các ô nhập của một thẻ từ vựng, dùng chung cho hộp Thêm thẻ và Sửa thẻ. */
export const CardFormFields: React.FC<CardFormFieldsProps> = ({ values, onChange, lang, showExamples = false }) => (
  <div className="flex flex-col gap-3.5">
    <FcInput
      label="Từ / Cụm từ ngoại ngữ (*)"
      type="text"
      required
      lang={lang}
      value={values.term}
      onChange={(e) => onChange({ term: e.target.value })}
      placeholder={showExamples ? "ví dụ: Implementation" : undefined}
    />
    <FcInput
      label="Nghĩa tiếng Việt (*)"
      type="text"
      required
      value={values.definition}
      onChange={(e) => onChange({ definition: e.target.value })}
      placeholder={showExamples ? "ví dụ: Sự triển khai, thực hiện" : undefined}
    />
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <FcInput
        label="Phiên âm IPA"
        type="text"
        mono
        value={values.phonetic}
        onChange={(e) => onChange({ phonetic: e.target.value })}
        placeholder={showExamples ? "/ˌɪm.plə.menˈteɪ.ʃən/" : undefined}
      />
      <FcSelect label="Từ loại" value={values.partOfSpeech} onChange={(e) => onChange({ partOfSpeech: e.target.value })}>
        <option value="noun">Danh từ (Noun)</option>
        <option value="verb">Động từ (Verb)</option>
        <option value="adjective">Tính từ (Adj)</option>
        <option value="phrase">Cụm từ (Phrase)</option>
      </FcSelect>
    </div>
    <FcInput
      label="Câu ví dụ ngữ cảnh"
      type="text"
      lang={lang}
      value={values.example}
      onChange={(e) => onChange({ example: e.target.value })}
      placeholder={showExamples ? "ví dụ: The implementation of AI in education." : undefined}
    />
  </div>
);

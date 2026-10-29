import colors from "tailwindcss/colors";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Màu chủ đạo duy nhất của giao diện (xanh dương nhẹ). Muốn đổi sắc xanh cả hệ thống: sửa ở đây.
        // Chỉ dùng cam cho "tín hiệu đặc biệt" (streak, cần ôn); cảnh báo dùng amber; lỗi dùng rose/red.
        brand: colors.blue,
      },
      keyframes: {
        // Rung nhẹ khi trả lời sai (thẻ trắc nghiệm/nghe)
        shake: {
          "0%, 100%": { transform: "translateX(0)" },
          "25%": { transform: "translateX(-5px)" },
          "75%": { transform: "translateX(5px)" },
        },
        // Mặt thẻ mới "lật" vào khi người học bấm lật thẻ (tôn trọng prefers-reduced-motion qua motion-reduce:animate-none)
        "flip-in": {
          "0%": { transform: "rotateY(90deg)", opacity: "0" },
          "100%": { transform: "rotateY(0deg)", opacity: "1" },
        },
      },
      animation: {
        "flip-in": "flip-in 0.28s ease-out",
      },
    },
  },
  plugins: [],
};

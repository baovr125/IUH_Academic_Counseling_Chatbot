/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
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

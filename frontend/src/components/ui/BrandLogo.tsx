import logoLight from "../../assets/brand/iuh-logo.png";
import logoDark from "../../assets/brand/iuh-logo-dark.png";

interface BrandLogoProps {
  /** Chiều cao (Tailwind), chiều rộng tự theo tỉ lệ. Mặc định `h-11`. */
  className?: string;
  alt?: string;
}

/**
 * Logo IUH trơn (nền trong suốt, không đặt trong ô riêng). Hai biến thể được chọn theo chế độ giao diện:
 * bản xanh navy cho nền sáng, bản xanh nhạt cho nền tối (navy trên nền tối chỉ đạt tương phản ~1.7:1).
 */
export function BrandLogo({ className = "h-11", alt = "" }: BrandLogoProps) {
  return (
    <>
      <img src={logoLight} alt={alt} width={225} height={264} draggable={false} className={`${className} w-auto object-contain dark:hidden`} />
      <img src={logoDark} alt={alt} width={225} height={264} draggable={false} className={`${className} hidden w-auto object-contain dark:block`} />
    </>
  );
}

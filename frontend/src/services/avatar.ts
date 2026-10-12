export const AVATAR_SIZE = 256;
export const AVATAR_MAX_INPUT_BYTES = 5 * 1024 * 1024;

/**
 * Đọc ảnh người dùng chọn, cắt vuông giữa ảnh và thu nhỏ về 256x256 (JPEG) rồi trả về data URL.
 * Server chỉ nhận data URL PNG/JPEG/WEBP tối đa ~200 KB nên việc thu nhỏ ở client là bắt buộc;
 * nó cũng loại bỏ SVG/GIF động và metadata EXIF trong ảnh gốc.
 */
export async function fileToAvatarDataUrl(file: File): Promise<string> {
  if (!file.type.startsWith("image/")) throw new Error("not-image");
  if (file.size > AVATAR_MAX_INPUT_BYTES) throw new Error("too-large");

  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = () => reject(new Error("decode-failed"));
      el.src = url;
    });
    const side = Math.min(img.naturalWidth, img.naturalHeight);
    if (!side) throw new Error("decode-failed");
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = AVATAR_SIZE;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("decode-failed");
    ctx.fillStyle = "#ffffff"; // nền trắng cho ảnh PNG trong suốt (JPEG không có alpha)
    ctx.fillRect(0, 0, AVATAR_SIZE, AVATAR_SIZE);
    const sx = (img.naturalWidth - side) / 2;
    const sy = (img.naturalHeight - side) / 2;
    ctx.drawImage(img, sx, sy, side, side, 0, 0, AVATAR_SIZE, AVATAR_SIZE);
    return canvas.toDataURL("image/jpeg", 0.85);
  } finally {
    URL.revokeObjectURL(url);
  }
}

import React from "react";
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { BrandLogo } from "../src/components/ui/BrandLogo";

describe("BrandLogo", () => {
  it("render hai biến thể: bản sáng ẩn khi dark, bản tối chỉ hiện khi dark", () => {
    const { container } = render(<BrandLogo className="h-10" alt="IUH" />);
    const imgs = container.querySelectorAll("img");
    expect(imgs).toHaveLength(2);
    expect(imgs[0].className).toContain("dark:hidden");
    expect(imgs[1].className).toContain("hidden");
    expect(imgs[1].className).toContain("dark:block");
    expect(imgs[0].getAttribute("src")).not.toEqual(imgs[1].getAttribute("src"));
  });

  it("nhận chiều cao qua className và mặc định h-11", () => {
    const a = render(<BrandLogo className="h-14" />).container.querySelector("img")!;
    expect(a.className).toContain("h-14");
    const b = render(<BrandLogo />).container.querySelector("img")!;
    expect(b.className).toContain("h-11");
  });
});

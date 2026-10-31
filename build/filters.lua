--[==[
Lua filter cho pandoc khi ghép báo cáo KLTN (gọi từ build_report.py).

Việc filter làm:
  * Heading: bỏ số viết tay ("CHƯƠNG 1.", "1.2", "2.3.1") vì Word tự đánh số
    theo style; đối chiếu số viết tay với số thực tế và cảnh báo nếu lệch.
    {.unnumbered} -> style "Heading 1N"/"Heading 2N" (không số, vẫn vào mục lục);
    {.unnumbered .unlisted} ở cấp 1 -> "Heading 1 Front" (không vào mục lục).
  * Hình: ![Hình 4.3. Chú thích](file.png) -> đoạn hình + caption dưới hình,
    số hiệu là trường STYLEREF/SEQ (Insert Caption của Word).
  * Bảng: đoạn "Bảng 3.5. Chú thích" ngay trên bảng -> caption trên bảng.
  * Công thức: $$ ... \tag{2-7} $$ -> công thức + đoạn số hiệu "(2-7)";
    build_report.py ghép hai đoạn này thành bảng 3 cột không viền.
  * Đoạn chỉ gồm [[TOC]] / [[LOF]] / [[LOT]] -> trường mục lục, danh mục hình, bảng.
  * Trích dẫn khối bắt đầu bằng [TODO hoặc [CHỜ SỐ LIỆU -> style "TODO" (nền vàng).

Metadata: caption-sep = colon (mặc định, "Hình 2.1: ...") | period ("Hình 2.1. ...").
]==]

local stringify = pandoc.utils.stringify

local caption_sep = ": "
local cnt = { 0, 0, 0, 0 }     -- bộ đếm heading cấp 1..4
local fig, tab = 0, 0           -- bộ đếm hình, bảng trong chương hiện tại
local appendix = nil            -- chữ cái của phụ lục hiện tại ("A", "B", …); nil khi đang ở chương
local n_eq, n_todo, n_warn = 0, 0, 0

local function warn(msg)
  n_warn = n_warn + 1
  io.stderr:write("[CẢNH BÁO] " .. msg .. "\n")
end

local function esc(s)
  return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"))
end

local function run(text)
  return '<w:r><w:t xml:space="preserve">' .. esc(text) .. '</w:t></w:r>'
end

local function field(instr, cached, dirty)
  local d = dirty and ' w:dirty="true"' or ''
  return '<w:r><w:fldChar w:fldCharType="begin"' .. d .. '/></w:r>'
      .. '<w:r><w:instrText xml:space="preserve"> ' .. esc(instr) .. ' </w:instrText></w:r>'
      .. '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
      .. run(cached)
      .. '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
end

local function raw(xml)
  return pandoc.RawBlock("openxml", xml)
end

-- "Hình 4.3. Abc" | "Hình 4.3: Abc" | "Hình x.y. Abc" -> "4.3", "Abc"
local function split_label(text, label)
  local num, rest = text:match("^" .. label .. "%s+([%dxA-Z]+%.[%dxy]+)[%.:]?%s+(.+)$")
  if num then return num, rest end
  return nil, text
end

local function check_number(label, given, n)
  local expected = (appendix or tostring(cnt[1])) .. "." .. n
  if given and not given:find("[xy]") and given ~= expected then
    warn(string.format("%s viết tay là %s nhưng số thực tế là %s", label, given, expected))
  end
end

local function caption_block(label, n, text, keep_next)
  local ppr = '<w:pPr><w:pStyle w:val="Caption"/>' .. (keep_next and '<w:keepNext/>' or '') .. '</w:pPr>'
  if appendix then
    -- Phụ lục: "Hình B.1". SEQ vẫn giữ để hình/bảng vào danh mục; \r 1 đặt lại bộ đếm ở đầu mỗi phụ lục.
    return raw('<w:p>' .. ppr .. run(label .. ' ' .. appendix .. '.')
      .. field('SEQ ' .. label .. ' \\* ARABIC' .. (n == 1 and ' \\r 1' or ''), tostring(n))
      .. run(caption_sep .. text) .. '</w:p>')
  end
  return raw('<w:p>' .. ppr .. run(label .. ' ')
    .. field('STYLEREF 1 \\s', tostring(cnt[1])) .. run('.')
    .. field('SEQ ' .. label .. ' \\* ARABIC \\s 1', tostring(n))
    .. run(caption_sep .. text) .. '</w:p>')
end

-- Heading ------------------------------------------------------------------
local CHUONG = { ["CHƯƠNG"] = true, ["Chương"] = true, ["chương"] = true }
local SEPS = { ["."] = true, [":"] = true, ["–"] = true, ["-"] = true, ["—"] = true }

local function strip_heading_number(inlines)
  local i = 1
  local function skip_space()
    while inlines[i] and (inlines[i].t == "Space" or inlines[i].t == "SoftBreak") do i = i + 1 end
  end
  local first, given = inlines[1], nil
  if first and first.t == "Str" and CHUONG[first.text] then
    i = 2
    skip_space()
    if inlines[i] and inlines[i].t == "Str" and inlines[i].text:match("^%d+[%.:]?$") then
      given = inlines[i].text:match("^(%d+)")
      i = i + 1
    end
  elseif first and first.t == "Str" and first.text:match("^%d+[%.%d]*$") then
    given = first.text:gsub("%.$", "")
    i = 2
  else
    return inlines, nil
  end
  skip_space()
  if inlines[i] and inlines[i].t == "Str" and SEPS[inlines[i].text] then
    i = i + 1
    skip_space()
  end
  local out = pandoc.Inlines({})
  for k = i, #inlines do out:insert(inlines[k]) end
  return out, given
end

local function on_header(b)
  local content, given = strip_heading_number(b.content)
  if b.level == 1 then
    -- Viết hoa sẵn để mục lục hiển thị giống tiêu đề (style chỉ in hoa khi hiển thị)
    content = content:walk({ Str = function(s) s.text = pandoc.text.upper(s.text); return s end })
  end
  if b.classes:includes("unnumbered") then
    if b.level == 1 then appendix = nil end
    local letter = b.level == 2 and stringify(content):match("^Phụ lục (%u)")
    if letter then appendix, fig, tab = letter, 0, 0 end
    local style
    if b.level == 1 then
      style = b.classes:includes("unlisted") and "Heading 1 Front" or "Heading 1N"
    elseif b.level == 2 then
      style = "Heading 2N"
    else
      warn("Heading không đánh số chỉ hỗ trợ cấp 1–2: " .. stringify(content))
      style = "Heading " .. b.level
    end
    return { pandoc.Div({ pandoc.Para(content) }, pandoc.Attr("", {}, { ["custom-style"] = style })) }
  end
  if b.level > 4 then
    warn("Mẫu của Khoa chỉ cho tối đa 4 cấp số: " .. stringify(content))
  end
  cnt[b.level] = (cnt[b.level] or 0) + 1
  for k = b.level + 1, 4 do cnt[k] = 0 end
  if b.level == 1 then fig, tab = 0, 0 end
  local parts = {}
  for k = 1, b.level do parts[#parts + 1] = tostring(cnt[k]) end
  local expected = table.concat(parts, ".")
  if given and given ~= expected then
    warn(string.format("Heading \"%s\" viết số %s nhưng số thực tế là %s", stringify(content), given, expected))
  end
  b.content = content
  return { b }
end

-- Hình ---------------------------------------------------------------------
local function on_figure(b)
  local num, text = split_label(stringify(b.caption.long), "Hình")
  fig = fig + 1
  check_number("Hình", num, fig)
  local imgs = pandoc.Inlines({})
  pandoc.walk_block(pandoc.Div(b.content), {
    Image = function(img)
      img.caption = pandoc.Inlines({})
      imgs:insert(img)
    end,
  })
  return {
    pandoc.Div({ pandoc.Para(imgs) }, pandoc.Attr("", {}, { ["custom-style"] = "Figure" })),
    caption_block("Hình", fig, text, false),
  }
end

-- Bảng ---------------------------------------------------------------------
local function on_table(tbl, captext)
  if not captext then
    captext = stringify(tbl.caption.long)
    if captext == "" then return { tbl } end
  end
  tbl.caption.long = pandoc.Blocks({})
  tab = tab + 1
  local num, text = split_label(captext, "Bảng")
  check_number("Bảng", num, tab)
  return { caption_block("Bảng", tab, text, true), tbl }
end

-- Công thức ----------------------------------------------------------------
local function equation_blocks(para)
  local m = nil
  for _, el in ipairs(para.content) do
    if el.t == "Math" and el.mathtype == "DisplayMath" and not m then
      m = el
    elseif el.t ~= "Space" and el.t ~= "SoftBreak" and el.t ~= "LineBreak" then
      return nil
    end
  end
  if not m then return nil end
  local tag = m.text:match("\\tag%s*{([^}]*)}")
  if not tag then return nil end
  m.text = m.text:gsub("\\tag%s*{[^}]*}", "")
  n_eq = n_eq + 1
  local c = tag:match("^(%d+)[%-%.]")
  if c and tonumber(c) ~= cnt[1] then
    warn(string.format("Công thức (%s) nằm ở chương %d", tag, cnt[1]))
  end
  return {
    pandoc.Para({ m }),
    raw('<w:p><w:pPr><w:pStyle w:val="EquationNumber"/></w:pPr>' .. run("(" .. tag .. ")") .. '</w:p>'),
  }
end

-- Mục lục, danh mục hình/bảng ------------------------------------------------
local TOC_FIELDS = {
  ["[[TOC]]"] = 'TOC \\o "1-3" \\h \\z \\u',
  ["[[LOF]]"] = 'TOC \\h \\z \\c "Hình"',
  ["[[LOT]]"] = 'TOC \\h \\z \\c "Bảng"',
}

local function toc_block(key)
  return raw('<w:p><w:pPr><w:pStyle w:val="Normal"/></w:pPr>'
    .. field(TOC_FIELDS[key], "Nhấn chuột phải → Update Field (hoặc Ctrl+A, F9) để cập nhật.", true)
    .. '</w:p>')
end

-- Ghi chú TODO -------------------------------------------------------------
local function on_blockquote(b)
  local s = stringify(b)
  if s:match("^%[TODO") or s:match("^%[CHỜ SỐ LIỆU") then
    n_todo = n_todo + 1
    return { pandoc.Div(b.content, pandoc.Attr("", {}, { ["custom-style"] = "TODO" })) }
  end
  return { b }
end

-- Bảng đặc tả use case ----------------------------------------------------------
-- Khối ```{.usecase caption="Bảng 3.x. Đặc tả use case ..."} với các dòng "Trường: giá trị".
-- Sau dòng "Luồng sự kiện chính:" mỗi bước là "A: ..." (tác nhân) hoặc "H: ..." (hệ thống);
-- sau dòng "Luồng sự kiện phụ:" mỗi dòng là một nhánh (3a. ..., 4a. ...).
local UC_FIELDS = { "Use case", "Mục đích", "Mô tả", "Tác nhân", "Điều kiện trước", "Điều kiện sau" }
local UC_MAIN, UC_ALT = "Luồng sự kiện chính", "Luồng sự kiện phụ"

local function md_blocks(text)
  local doc = pandoc.read(text, "markdown")
  local blocks = pandoc.Blocks({})
  for _, blk in ipairs(doc.blocks) do
    if blk.t == "Para" then blocks:insert(pandoc.Plain(blk.content)) else blocks:insert(blk) end
  end
  return blocks
end

local function uc_cell(blocks, rowspan, colspan)
  return pandoc.Cell(blocks, "AlignDefault", rowspan or 1, colspan or 1)
end

local function label(text)
  return pandoc.Blocks({ pandoc.Plain({ pandoc.Strong({ pandoc.Str(text) }) }) })
end

local function usecase_table(code)
  local fields, steps, alts, mode = {}, {}, {}, "fields"
  for line in (code .. "\n"):gmatch("(.-)\r?\n") do
    local trimmed = line:match("^%s*(.-)%s*$")
    if trimmed ~= "" then
      if trimmed == UC_MAIN .. ":" then
        mode = "main"
      elseif trimmed == UC_ALT .. ":" then
        mode = "alt"
      elseif mode == "main" then
        local who, text = trimmed:match("^([AH]):%s*(.+)$")
        if who then steps[#steps + 1] = { who = who, text = text }
        else warn("Dòng luồng chính không bắt đầu bằng A: hoặc H:: " .. trimmed) end
      elseif mode == "alt" then
        alts[#alts + 1] = trimmed
      else
        local matched = false
        for _, key in ipairs(UC_FIELDS) do
          local prefix = key .. ":"
          if trimmed:sub(1, #prefix) == prefix then
            fields[key] = trimmed:sub(#prefix + 1):match("^%s*(.-)$")
            matched = true
          end
        end
        if not matched then warn("Trường đặc tả use case không hợp lệ: " .. trimmed) end
      end
    end
  end
  local head_rows, rows = {}, {}
  for i, key in ipairs(UC_FIELDS) do
    if fields[key] then
      local row = pandoc.Row({ uc_cell(label(key)), uc_cell(md_blocks(fields[key]), 1, 2) })
      if i == 1 then head_rows[#head_rows + 1] = row else rows[#rows + 1] = row end
    end
  end
  if #steps > 0 then
    -- Mỗi hàng là một lượt: các bước của tác nhân và phản hồi của hệ thống nằm cạnh nhau.
    local turns = {}
    for _, s in ipairs(steps) do
      local cur = turns[#turns]
      if not cur or (s.who == "A" and #cur.H > 0) then
        cur = { A = pandoc.Blocks({}), H = pandoc.Blocks({}) }
        turns[#turns + 1] = cur
      end
      -- "1. ..." giữ nguyên số thứ tự, không để pandoc đọc thành danh sách thụt lề.
      for _, blk in ipairs(md_blocks((s.text:gsub("^(%d+)%.", "%1\\.")))) do
        cur[s.who]:insert(blk.t == "Plain" and pandoc.Para(blk.content) or blk)
      end
    end
    rows[#rows + 1] = pandoc.Row({ uc_cell(label(UC_MAIN), #turns + 1, 1),
      uc_cell(label("Tác nhân")), uc_cell(label("Hệ thống")) })
    for _, t in ipairs(turns) do
      rows[#rows + 1] = pandoc.Row({ uc_cell(t.A), uc_cell(t.H) })
    end
  end
  if #alts > 0 then
    local blocks = pandoc.Blocks({})
    for _, a in ipairs(alts) do
      for _, blk in ipairs(md_blocks(a)) do
        blocks:insert(blk.t == "Plain" and pandoc.Para(blk.content) or blk)
      end
    end
    rows[#rows + 1] = pandoc.Row({ uc_cell(label(UC_ALT)), uc_cell(blocks, 1, 2) })
  end
  local colspecs = { { "AlignDefault", 0.22 }, { "AlignDefault", 0.39 }, { "AlignDefault", 0.39 } }
  return pandoc.Table({ long = pandoc.Blocks({}) }, colspecs, pandoc.TableHead(head_rows),
    { { attr = pandoc.Attr(), body = rows, head = {}, row_head_columns = 0 } }, pandoc.TableFoot())
end

-- Duyệt tuần tự để giữ đúng thứ tự chương/hình/bảng -----------------------------
local process

process = function(blocks)
  local out = pandoc.Blocks({})
  local i = 1
  while i <= #blocks do
    local b, nxt = blocks[i], blocks[i + 1]
    if b.t == "Header" then
      out:extend(on_header(b))
    elseif b.t == "Figure" then
      out:extend(on_figure(b))
    elseif b.t == "Table" then
      out:extend(on_table(b, nil))
    elseif b.t == "Para" then
      local s = stringify(b)
      if TOC_FIELDS[s] then
        out:insert(toc_block(s))
      elseif nxt and nxt.t == "Table" and s:match("^Bảng%s") then
        out:extend(on_table(nxt, s))
        i = i + 1
      else
        out:extend(equation_blocks(b) or { b })
      end
    elseif b.t == "CodeBlock" and b.classes:includes("usecase") then
      out:extend(on_table(usecase_table(b.text), b.attributes.caption or ""))
    elseif b.t == "BlockQuote" then
      out:extend(on_blockquote(b))
    elseif b.t == "Div" then
      b.content = process(b.content)
      out:insert(b)
    else
      out:insert(b)
    end
    i = i + 1
  end
  return out
end

function Pandoc(doc)
  if doc.meta["caption-sep"] and stringify(doc.meta["caption-sep"]) == "period" then
    caption_sep = ". "
  end
  doc.blocks = process(doc.blocks)
  io.stderr:write(string.format("[filter] %d chương, %d công thức đánh số, %d ghi chú TODO, %d cảnh báo\n",
    cnt[1], n_eq, n_todo, n_warn))
  return doc
end

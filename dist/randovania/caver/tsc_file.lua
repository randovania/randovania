local TscFile = {}

function TscFile:new(contents)
  o = {}
  setmetatable(o, self)
  self.__index = self
  self._text = self:_codec(contents, 'decode')
  return o
end

function TscFile:placeScriptAtEvent(script, event, mapname, needle)
  needle = needle or "<EVE...."
  local err
  self._text, err = self:_stringReplace(self._text, needle, script, event)
  if err ~= nil then
    local template = 'Unable to place script "%s" at [%s] event "%s".\nCause: %s'
    error(template:format(script, mapname, event, err))
  end
end

function TscFile:placeSongAtCue(songid, event, originalid, mapname)
  local err
  self._text, err = self:_stringReplace(self._text, "<CMU" .. originalid, "<CMU" .. songid, event, {"<CMU0015", "<CMU0000"})
  if err ~= nil then
    local template = "Unable to replace [%s] event #%s's music cue with %q.\nCause: %s"
    error(template:format(mapname, event, songid, err))
  end
end

function TscFile:_stringReplace(text, needle, replacement, label, overrides)
  overrides = overrides or {}
  local pStart, pEnd = self:_getLabelPositionRange(label)

  local i, o = -1, -1
  while(o <= i) do
    o = nil
    i, i2 = text:find(needle, pStart)

    if i == nil then
      local err = ('No match for "%s".'):format(needle)
      return text, err
    elseif i > pEnd then
      -- This is totally normal and can be ignored.
      local err = ('Found "%s", but was outside of label (%d, %d) at index %d.'):format(needle, pStart, pEnd, i)
      return text, err
    end

    -- find the earliest occurence of an override
    for k,v in ipairs(overrides) do
      local over = text:find(v, pStart)
      if over ~= nil then
        if o ~= nil then
          o = math.min(o, over)
        else
          o = over
        end
      end
    end

    -- no overrides found
    if o == nil then break end

    pStart = o+1
  end

  local len = i2-i+1
  local j = i + len - 1
  assert((i % 1 == 0) and (i > 0) and (i <= j), tostring(i))
  assert((j % 1 == 0), tostring(j))
  local a = text:sub(1, i - 1)
  local b = text:sub(j + 1)
  return a .. replacement .. b, nil
end

function TscFile:_getLabelPositionRange(label)
  local labelStart, labelEnd

  -- Recursive shit for when label is a table...
  if type(label) == 'table' then
    labelStart, labelEnd = math.huge, 0
    for _, _label in ipairs(label) do
      local _start, _end = self:_getLabelPositionRange(_label)
      labelStart = math.min(labelStart, _start)
      labelEnd   = math.max(labelEnd,   _end)
    end
    return labelStart, labelEnd
  end

  assert(type(label) == 'string')
  assert(#label == 4)
  assert(tonumber(label) >= 0)
  assert(tonumber(label) <= 9999)

  local i = 1
  local labelPattern = "#%d%d%d%d\r\n"
  while true do
    local j = self._text:find(labelPattern, i)
    if j == nil then
      break
    end
    i = j + 1

    if labelStart then
      labelEnd = j - 1
      break
    end

    local _label = self._text:sub(j + 1, j + 4)
    if label == _label then
      labelStart = j
    end
  end

  if labelStart == nil then
    error(("%s: Could not find label: %s"):format(self.mapName, label))
    labelStart = 1
  end

  if labelEnd == nil then
    labelEnd = #self._text
  end

  return labelStart, labelEnd
end

function TscFile:getPlaintext()
  return self._text
end

function TscFile:getText()
  return self:_codec(self._text, 'encode')
end

function TscFile:_codec(text, mode)
  -- Create array of chars.
  local chars = {}
  text:gsub(".", function(c) table.insert(chars, c) end)

  -- Determine encoding char value
  local encodingCharPosition = math.floor(#chars / 2) + 1
  local encodingChar = chars[encodingCharPosition]:byte()
  if mode == 'decode' then
    encodingChar = encodingChar * -1
  elseif mode == 'encode' then
    -- OK!
  else
    error('Unknown codec mode: ' .. tostring(mode))
  end

  -- Encode or decode.
  for pos, char in ipairs(chars) do
    if pos ~= encodingCharPosition then
      local byte = (char:byte() + encodingChar) % 256
      if mode == 'decode' then
        chars[pos] = string.char(byte)
      else
        chars[pos] = byte
      end
    elseif mode == 'encode' then
      chars[pos] = char:byte()
    end
  end
  if mode == 'encode' then
    return chars
  end
  return table.concat(chars)
end

return TscFile

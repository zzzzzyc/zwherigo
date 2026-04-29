require "Wherigo"
ZonePoint = Wherigo.ZonePoint
Distance = Wherigo.Distance
Player = Wherigo.Player

-- String decode --
function _AR0fF(str)
	local res = ""
    local dtable = "\121\002\098\113\112\084\086\122\067\071\006\028\049\103\011\075\045\048\022\064\099\012\047\073\072\033\052\041\092\035\017\023\090\014\080\056\069\066\119\050\015\055\058\083\013\115\093\009\118\095\063\031\125\039\029\034\024\091\040\060\097\068\038\107\059\036\016\054\005\065\030\074\057\042\026\027\062\088\021\076\104\124\096\102\044\116\123\008\105\003\077\120\081\070\114\101\007\089\025\004\051\106\000\061\018\001\032\108\111\053\100\082\010\117\037\110\079\109\019\094\046\126\078\085\087\043\020"
	for i=1, #str do
        local b = str:byte(i)
        if b > 0 and b <= 0x7F then
	        res = res .. string.char(dtable:byte(b))
        else
            res = res .. string.char(b)
        end
	end
	return res
end

-- Internal functions --
require "table"
require "math"

math.randomseed(os.time())
math.random()
math.random()
math.random()

_Urwigo = {}

_Urwigo.InlineRequireLoaded = {}
_Urwigo.InlineRequireRes = {}
_Urwigo.InlineRequire = function(moduleName)
  local res
  if _Urwigo.InlineRequireLoaded[moduleName] == nil then
    res = _Urwigo.InlineModuleFunc[moduleName]()
    _Urwigo.InlineRequireLoaded[moduleName] = 1
    _Urwigo.InlineRequireRes[moduleName] = res
  else
    res = _Urwigo.InlineRequireRes[moduleName]
  end
  return res
end

_Urwigo.Round = function(num, idp)
  local mult = 10^(idp or 0)
  return math.floor(num * mult + 0.5) / mult
end

_Urwigo.Ceil = function(num, idp)
  local mult = 10^(idp or 0)
  return math.ceil(num * mult) / mult
end

_Urwigo.Floor = function(num, idp)
  local mult = 10^(idp or 0)
  return math.floor(num * mult) / mult
end

_Urwigo.DialogQueue = {}
_Urwigo.RunDialogs = function(callback)
	local dialogs = _Urwigo.DialogQueue
	local lastCallback = nil
	_Urwigo.DialogQueue = {}
	local msgcb = {}
	msgcb = function(action)
		if action ~= nil then
			if lastCallback ~= nil then
				lastCallback(action)
			end
			local entry = table.remove(dialogs, 1)
			if entry ~= nil then
				lastCallback = entry.Callback;
				if entry.Text ~= nil then
					Wherigo.MessageBox({Text = entry.Text, Media=entry.Media, Buttons=entry.Buttons, Callback=msgcb})
				else
					msgcb(action)
				end
			else
				if callback ~= nil then
					callback()
				end
			end
		end
	end
	msgcb(true) -- any non-null argument
end

_Urwigo.MessageBox = function(tbl)
    _Urwigo.RunDialogs(function() Wherigo.MessageBox(tbl) end)
end

_Urwigo.OldDialog = function(tbl)
    _Urwigo.RunDialogs(function() Wherigo.Dialog(tbl) end)
end

_Urwigo.Dialog = function(buffered, tbl, callback)
	for k,v in ipairs(tbl) do
		table.insert(_Urwigo.DialogQueue, v)
	end
	if callback ~= nil then
		table.insert(_Urwigo.DialogQueue, {Callback=callback})
	end
	if not buffered then
		_Urwigo.RunDialogs(nil)
	end
end

_Urwigo.Hash = function(str)
   local b = 378551;
   local a = 63689;
   local hash = 0;
   for i = 1, #str, 1 do
      hash = hash*a+string.byte(str,i);
      hash = math.fmod(hash, 65535)
      a = a*b;
      a = math.fmod(a, 65535)
   end
   return hash;
end

_Urwigo.DaysInMonth = {
	31,
	28,
	31,
	30,
	31,
	30,
	31,
	31,
	30,
	31,
	30,
	31,
}

_Urwigo_Date_IsLeapYear = function(year)
	if year % 400 == 0 then
		return true
	elseif year% 100 == 0 then
		return false
	elseif year % 4 == 0 then
		return true
	else
		return false
	end
end

_Urwigo.Date_DaysInMonth = function(year, month)
	if month ~= 2 then
		return _Urwigo.DaysInMonth[month];
	else
		if _Urwigo_Date_IsLeapYear(year) then
			return 29
		else
			return 28
		end
	end
end

_Urwigo.Date_DayInYear = function(t)
	local res = t.day
	for month = 1, t.month - 1 do
		res = res + _Urwigo.Date_DaysInMonth(t.year, month)
	end
	return res
end

_Urwigo.Date_HourInWeek = function(t)
	return t.hour + (t.wday-1) * 24
end

_Urwigo.Date_HourInMonth = function(t)
	return t.hour + t.day * 24
end

_Urwigo.Date_HourInYear = function(t)
	return t.hour + (_Urwigo.Date_DayInYear(t) - 1) * 24
end

_Urwigo.Date_MinuteInDay = function(t)
	return t.min + t.hour * 60
end

_Urwigo.Date_MinuteInWeek = function(t)
	return t.min + t.hour * 60 + (t.wday-1) * 1440;
end

_Urwigo.Date_MinuteInMonth = function(t)
	return t.min + t.hour * 60 + (t.day-1) * 1440;
end

_Urwigo.Date_MinuteInYear = function(t)
	return t.min + t.hour * 60 + (_Urwigo.Date_DayInYear(t) - 1) * 1440;
end

_Urwigo.Date_SecondInHour = function(t)
	return t.sec + t.min * 60
end

_Urwigo.Date_SecondInDay = function(t)
	return t.sec + t.min * 60 + t.hour * 3600
end

_Urwigo.Date_SecondInWeek = function(t)
	return t.sec + t.min * 60 + t.hour * 3600 + (t.wday-1) * 86400
end

_Urwigo.Date_SecondInMonth = function(t)
	return t.sec + t.min * 60 + t.hour * 3600 + (t.day-1) * 86400
end

_Urwigo.Date_SecondInYear = function(t)
	return t.sec + t.min * 60 + t.hour * 3600 + (_Urwigo.Date_DayInYear(t)-1) * 86400
end


-- Inlined modules --
_Urwigo.InlineModuleFunc = {}

_ZgAaB = Wherigo.ZCartridge()

-- Media --
-- Cartridge Info --
_ZgAaB.Id="a9564529-c2a8-466b-902e-b7710ae2cc8b"
_ZgAaB.Name="shougang's lost item"
_ZgAaB.Description=[[[ONLY CHINESE]

The roar of the blast furnace has long since ceased, and the once scorching steel giant now sleeps in silence. But if you listen closely, deep within those mottled pipes, there still seems to be a faint signal from the old era flickering.  
You will act as a treasure hunter of the new era, following the clues left by the old-generation Shougang foremen to find the maintenance terminals and portable base stations that were left behind. Reestablish connections in this steel forest, and follow the string of constantly flashing distance numbers to retrieve the 'core component' that time has buried.]]
_ZgAaB.Visible=true
_ZgAaB.Activity="Geocache"
_ZgAaB.StartingLocationDescription=[[至少位于北京市石景山区
]]
_ZgAaB.StartingLocation = Wherigo.INVALID_ZONEPOINT
_ZgAaB.Version="0.1.0"
_ZgAaB.Company=""
_ZgAaB.Author="zzzzzyc"
_ZgAaB.BuilderVersion="URWIGO 1.22.5798.37755"
_ZgAaB.CreateDate="04/29/2026 02:43:52"
_ZgAaB.PublishDate="1/1/0001 12:00:00 AM"
_ZgAaB.UpdateDate="04/29/2026 17:23:34"
_ZgAaB.LastPlayedDate="1/1/0001 12:00:00 AM"
_ZgAaB.TargetDevice="PocketPC"
_ZgAaB.TargetDeviceVersion="0"
_ZgAaB.StateId="1"
_ZgAaB.CountryId="2"
_ZgAaB.Complete=false
_ZgAaB.UseLogging=true


-- Zones --
_lLQrR = Wherigo.Zone(_ZgAaB)
_lLQrR.Id = "b959f16c-5eac-4836-85d7-0bc977ad66d0"
_lLQrR.Name = _AR0fF("\231\187\136\231\171\175\232\151\143\229\140\191\231\130\185")
_lLQrR.Description = _AR0fF("\228\189\160\232\174\176\229\190\151\228\189\160\229\156\168\232\191\153\233\135\140\232\151\143\228\186\134\228\184\128\228\184\170\230\137\139\230\140\129\231\187\136\231\171\175\239\188\140\231\142\176\229\156\168\232\175\183\229\137\141\229\190\128\229\175\187\230\137\190\229\174\131\060\038\112\077\227\128\144\228\189\141\231\189\174\239\188\154\229\133\171\232\167\146\230\184\184\228\185\144\229\155\173\233\151\168\229\137\141\229\185\191\229\156\186\227\128\145")
_lLQrR.Visible = true
_lLQrR.Commands = {}
_lLQrR.DistanceRange = Distance(-1, "feet")
_lLQrR.ShowObjects = "OnEnter"
_lLQrR.ProximityRange = Distance(60, "meters")
_lLQrR.AllowSetPositionTo = false
_lLQrR.Active = false
_lLQrR.Points = {
	ZonePoint(39.907571474698, 116.200290212465, 0), 
	ZonePoint(39.9068350530494, 116.200349527623, 0), 
	ZonePoint(39.9064814621509, 116.202173780554, 0), 
	ZonePoint(39.9069134260117, 116.20324510958, 0), 
	ZonePoint(39.9075183211687, 116.203068861446, 0)
}
_lLQrR.OriginalPoint = ZonePoint(39.9070639474157, 116.201825498334, 0)
_lLQrR.DistanceRangeUOM = "Feet"
_lLQrR.ProximityRangeUOM = "Meters"
_lLQrR.OutOfRangeName = ""
_lLQrR.InRangeName = ""
_KQwil = Wherigo.Zone(_ZgAaB)
_KQwil.Id = "0dd770cd-021d-4b53-afa4-9a9880255050"
_KQwil.Name = _AR0fF("\229\164\135\231\148\168\229\159\186\231\171\153")
_KQwil.Description = _AR0fF("\228\189\160\228\190\157\231\168\128\232\174\176\229\190\151\229\156\168\232\128\129\229\177\177\231\154\132\231\158\173\230\156\155\229\143\176\233\153\132\232\191\145\230\156\137\228\184\170\229\164\135\231\148\168\229\159\186\231\171\153\239\188\140\230\156\137\228\186\134\229\174\131\228\189\160\229\176\177\232\131\189\229\174\154\228\189\141\233\155\182\228\187\182\239\188\129")
_KQwil.Visible = true
_KQwil.Commands = {}
_KQwil.DistanceRange = Distance(-1, "feet")
_KQwil.ShowObjects = "OnEnter"
_KQwil.ProximityRange = Distance(60, "meters")
_KQwil.AllowSetPositionTo = false
_KQwil.Active = false
_KQwil.Points = {
	ZonePoint(39.9153208617478, 116.21683249525, 0), 
	ZonePoint(39.9152883074633, 116.217316356856, 0), 
	ZonePoint(39.9149888073195, 116.217469155258, 0), 
	ZonePoint(39.9146176857593, 116.21761346486, 0), 
	ZonePoint(39.9143377155322, 116.217554043259, 0), 
	ZonePoint(39.9141814525822, 116.217146580854, 0), 
	ZonePoint(39.914122853884, 116.216688185648, 0), 
	ZonePoint(39.9141358758213, 116.216255256843, 0), 
	ZonePoint(39.9143181826829, 116.215898727239, 0), 
	ZonePoint(39.9145981529899, 116.215618596836, 0), 
	ZonePoint(39.9152492423014, 116.215754417637, 0), 
	ZonePoint(39.9153729485709, 116.216323167244, 0)
}
_KQwil.OriginalPoint = ZonePoint(39.9147110072212, 116.216705870649, 0)
_KQwil.DistanceRangeUOM = "Feet"
_KQwil.ProximityRangeUOM = "Meters"
_KQwil.OutOfRangeName = ""
_KQwil.InRangeName = ""
_fa8 = Wherigo.Zone(_ZgAaB)
_fa8.Id = "a2a42a63-0c2a-433a-b160-b4f93200111e"
_fa8.Name = _AR0fF("\231\187\136\231\130\185")
_fa8.Description = _AR0fF("\232\191\153\233\135\140\229\176\177\230\152\175\231\187\136\231\130\185\228\186\134\239\188\129\233\155\182\228\187\182\231\154\132\228\189\141\231\189\174\239\188\140\228\185\159\230\152\175\229\174\157\232\151\143\231\154\132\228\189\141\231\189\174\060\038\112\077")
_fa8.Visible = false
_fa8.Commands = {}
_fa8.DistanceRange = Distance(-1, "feet")
_fa8.ShowObjects = "OnEnter"
_fa8.ProximityRange = Distance(60, "meters")
_fa8.AllowSetPositionTo = false
_fa8.Active = false
_fa8.Points = {
	ZonePoint(39.9029051872142, 116.199721541422, 0), 
	ZonePoint(39.9029529653131, 116.200299006152, 0), 
	ZonePoint(39.9031586150838, 116.200463249892, 0), 
	ZonePoint(39.9033898313165, 116.200065115883, 0), 
	ZonePoint(39.9032559154158, 116.199496438355, 0)
}
_fa8.OriginalPoint = ZonePoint(39.9031325028687, 116.200009070341, 0)
_fa8.DistanceRangeUOM = "Feet"
_fa8.ProximityRangeUOM = "Meters"
_fa8.OutOfRangeName = ""
_fa8.InRangeName = ""

-- Characters --

-- Items --
_E7Yob = Wherigo.ZItem(_ZgAaB)
_E7Yob.Id = "b9cd1156-30eb-4693-88fb-fb09e4a8a03e"
_E7Yob.Name = _AR0fF("\230\151\160\231\189\145\231\187\156\231\154\132\231\187\136\231\171\175")
_E7Yob.Description = _AR0fF("\228\189\160\230\137\190\229\136\176\228\186\134\231\187\136\231\171\175\239\188\140\229\143\175\230\131\156\229\174\131\230\151\160\231\189\145\231\187\156\239\188\129")
_E7Yob.Visible = true
_E7Yob.Commands = {
	_Nm1x = Wherigo.ZCommand{
		Text = _AR0fF("\230\159\165\231\156\139\229\177\143\229\185\149"), 
		CmdWith = false, 
		Enabled = true, 
		EmptyTargetListText = _AR0fF("\123\109\086\081\089\116\014\107\061\049\061\089\108\061\003\108\096")
	}
}
_E7Yob.Commands._Nm1x.Custom = true
_E7Yob.Commands._Nm1x.Id = "d8643d7f-7dab-4a44-bc31-8b9fd384c141"
_E7Yob.Commands._Nm1x.WorksWithAll = true
_E7Yob.ObjectLocation = Wherigo.INVALID_ZONEPOINT
_E7Yob.Locked = false
_E7Yob.Opened = false
_Jvuml = Wherigo.ZItem(_ZgAaB)
_Jvuml.Id = "ea9b9fc3-06e4-41a4-8c24-060636a7d820"
_Jvuml.Name = _AR0fF("\231\187\136\231\171\175")
_Jvuml.Description = _AR0fF("\229\183\178\231\187\143\228\184\138\231\186\191\231\154\132\231\187\136\231\171\175\239\188\140\233\151\170\231\157\128\229\185\189\229\185\189\232\147\157\229\133\137\239\188\140\232\191\153\228\184\170\231\138\182\230\128\129\229\143\175\228\187\165\229\174\154\228\189\141\233\155\182\228\187\182")
_Jvuml.Visible = true
_Jvuml.Commands = {
	_5e3 = Wherigo.ZCommand{
		Text = _AR0fF("\230\159\165\231\156\139\229\177\143\229\185\149"), 
		CmdWith = false, 
		Enabled = true, 
		EmptyTargetListText = ""
	}
}
_Jvuml.Commands._5e3.Custom = true
_Jvuml.Commands._5e3.Id = "217e10dd-f241-4007-b647-d1f804eb7673"
_Jvuml.Commands._5e3.WorksWithAll = true
_Jvuml.ObjectLocation = Wherigo.INVALID_ZONEPOINT
_Jvuml.Locked = false
_Jvuml.Opened = false
_MDT3h = Wherigo.ZItem(_ZgAaB)
_MDT3h.Id = "c9ce162a-284a-486a-aa88-8189a3728048"
_MDT3h.Name = _AR0fF("\229\164\135\229\191\152\229\189\149")
_MDT3h.Description = _AR0fF("\228\189\160\232\191\152\232\174\176\229\190\151\233\155\182\228\187\182\232\151\143\229\156\168\228\186\134\228\184\128\228\184\170\229\134\153\231\157\128\060\038\112\077\226\128\156\060\038\112\077\226\134\144\230\163\174\230\158\151\229\173\166\229\160\130\107\063\116\003\046\005\065\229\141\151\229\133\165\229\143\163\226\134\146\060\038\112\077\226\134\144\230\157\190\230\158\156\230\172\162\228\185\144\229\155\173\107\229\141\171\231\148\159\233\151\180\226\134\145\060\038\112\077\226\134\144\231\171\165\231\170\157\232\182\163\060\038\112\077\226\128\157\060\038\112\077\231\154\132\232\183\175\231\137\140\230\151\129\060\038\112\077\233\130\163\233\135\140\229\186\148\232\175\165\230\156\137\230\149\176\229\157\151\231\159\179\229\164\180\239\188\140\229\174\131\229\176\177\230\152\175\228\184\128\229\157\151\229\129\135\231\159\179\229\164\180\239\188\140\232\162\171\231\162\142\231\159\179\229\141\138\230\142\169\229\156\168\229\164\167\231\159\179\229\164\180\228\185\139\229\144\142\060\038\112\077\230\137\190\229\136\176\229\174\131\239\188\140\231\173\190\228\184\138\228\189\160\231\154\132\229\164\167\229\144\141\239\188\140\228\186\164\230\141\162\014\096\109\021\109\089\116\239\188\140\108\109\014\107\084\089\116\111\239\188\140\228\186\171\229\143\151\232\142\183\232\131\156\232\128\133\229\186\148\229\190\151\231\154\132\232\141\163\232\170\137\229\144\167\239\188\129")
_MDT3h.Visible = true
_MDT3h.Commands = {}
_MDT3h.ObjectLocation = Wherigo.INVALID_ZONEPOINT
_MDT3h.Locked = false
_MDT3h.Opened = false

-- Tasks --
_sF4a = Wherigo.ZTask(_ZgAaB)
_sF4a.Id = "ee1246ba-c86a-479c-9ac4-1b1404c7e75c"
_sF4a.Name = _AR0fF("\229\175\187\230\137\190\231\187\136\231\171\175")
_sF4a.Description = _AR0fF("\229\143\170\232\166\129\230\137\190\229\136\176\231\187\136\231\171\175\239\188\140\228\184\128\229\136\135\233\131\189\228\188\154\229\165\189\232\181\183\230\157\165\231\154\132")
_sF4a.Visible = true
_sF4a.Active = false
_sF4a.Complete = false
_sF4a.CorrectState = "None"
_46MF = Wherigo.ZTask(_ZgAaB)
_46MF.Id = "cf08e349-ab81-4fa7-9ff6-bcfc7a48bcc4"
_46MF.Name = _AR0fF("\229\175\187\230\137\190\229\159\186\231\171\153")
_46MF.Description = _AR0fF("\228\189\160\230\137\190\229\136\176\228\186\134\231\187\136\231\171\175\239\188\140\229\143\175\230\131\156\230\178\161\230\156\137\231\189\145\231\187\156\230\151\160\230\179\149\229\174\154\228\189\141\233\155\182\228\187\182\239\188\140\229\185\184\229\165\189\228\189\160\232\191\152\232\174\176\229\190\151\228\184\128\228\184\170\229\164\135\231\148\168\229\159\186\231\171\153\231\154\132\228\189\141\231\189\174")
_46MF.Visible = true
_46MF.Active = false
_46MF.Complete = false
_46MF.CorrectState = "None"
_mXW = Wherigo.ZTask(_ZgAaB)
_mXW.Id = "47c3e299-2a62-4024-b44a-1aaee2e80523"
_mXW.Name = _AR0fF("\229\175\187\230\137\190\233\155\182\228\187\182")
_mXW.Description = _AR0fF("\231\187\136\228\186\142\239\188\140\230\136\145\228\187\172\229\143\175\228\187\165\229\174\154\228\189\141\233\155\182\228\187\182\228\186\134\239\188\129\060\038\112\077\239\188\136\228\189\191\231\148\168\231\187\136\231\171\175\230\157\165\232\142\183\229\143\150\232\183\157\231\166\187\239\188\137")
_mXW.Visible = true
_mXW.Active = false
_mXW.Complete = false
_mXW.CorrectState = "None"

-- Cartridge Variables --
_EBu0a = _AR0fF("\050\108\080\093\095\112")
_c7a = _AR0fF("\111\114\118\118\001")
_l8f = _AR0fF("\050\037\042\098\109\003")
_3Cfw5 = _AR0fF("\050\046\094\027\061")
_vR9ww = _AR0fF("\111\114\118\118\001")
_ASS0Y = _AR0fF("\111\114\118\118\001")
_ZgAaB.ZVariables = {
	_EBu0a = _AR0fF("\050\108\080\093\095\112"), 
	_c7a = _AR0fF("\111\114\118\118\001"), 
	_l8f = _AR0fF("\050\037\042\098\109\003"), 
	_3Cfw5 = _AR0fF("\050\046\094\027\061"), 
	_vR9ww = _AR0fF("\111\114\118\118\001"), 
	_ASS0Y = _AR0fF("\111\114\118\118\001")
}

-- Timers --

-- Inputs --

-- WorksWithList for object commands --

-- functions --
function _ZgAaB:OnStart()
	_Urwigo.MessageBox{
		Text = _AR0fF("\058\117\123\080\098\107\009\025\024\123\037\044\037\047\060\038\112\077\228\189\160\229\165\189\239\188\129\060\038\112\077\228\189\160\230\152\175\228\184\128\229\144\141\229\183\165\231\168\139\229\184\136\239\188\140\233\166\150\233\146\162\230\144\172\232\191\129\229\137\141\228\189\160\229\156\168\232\191\153\232\190\185\232\151\143\228\186\134\228\184\128\228\184\170\233\155\182\228\187\182\239\188\140\231\142\176\229\156\168\229\191\152\228\186\134\229\156\168\229\147\170\228\186\134\239\188\140\229\185\184\228\186\143\228\189\160\232\191\152\230\156\137\228\184\128\228\184\170\230\137\139\230\140\129\231\187\136\231\171\175\229\143\175\228\187\165\228\189\191\231\148\168\239\188\140\228\187\150\228\188\154\229\184\174\228\189\160\229\174\154\228\189\141\060\038\112\077\231\142\176\229\156\168\239\188\140\229\142\187\230\139\191\229\155\158\228\189\160\231\154\132\231\187\136\231\171\175\229\144\167"), 
		Buttons = {
			_AR0fF("\229\149\165\239\188\159")
		}, 
		Callback = function(action)
			if action ~= nil then
				_Urwigo.MessageBox{
					Text = _AR0fF("\228\184\141\232\166\129\231\174\161\229\137\167\230\131\133\229\144\136\231\144\134\230\128\167\239\188\129\230\136\145\230\178\161\230\156\137\232\182\179\229\164\159\231\154\132\230\150\135\233\135\135\229\134\153\228\184\128\228\186\155\229\165\189\231\154\132\229\137\167\230\131\133\060\038\112\077\228\184\141\231\174\161\229\166\130\228\189\149\239\188\140\232\191\153\233\135\140\230\156\137\228\184\128\228\186\155\230\156\137\231\148\168\231\154\132\230\143\144\233\134\146\239\188\154\060\038\112\077\013\121\228\184\141\232\166\129\231\155\184\228\191\161\061\005\005\231\154\132\229\156\176\229\155\190\239\188\140\228\189\134\230\152\175\229\143\175\228\187\165\231\155\184\228\191\161\231\189\151\231\155\152\060\038\112\077\040\121\231\155\184\228\191\161\230\136\145\107\229\188\128\228\184\170\232\189\166\023\233\170\145\228\184\170\231\148\181\233\169\180\060\038\112\077\101\121\232\166\129\228\184\141\233\161\186\228\190\191\230\137\147\228\184\128\228\184\139\233\161\186\232\183\175\231\154\132\229\174\157\043\028\060\038\112\077\060\038\112\077"), 
					Buttons = {
						_AR0fF("\227\128\130\227\128\130\227\128\130")
					}
				}
			end
		end
	}
	_lLQrR.Active = true
	_sF4a.Active = true
end
function _ZgAaB:OnRestore()
end
function _lLQrR:OnEnter()
	_EBu0a = _AR0fF("\050\108\080\093\095\112")
	_Urwigo.MessageBox{
		Text = _AR0fF("\228\189\160\229\136\176\228\186\134\232\174\176\229\191\134\228\184\173\231\154\132\231\187\136\231\171\175\232\151\143\229\140\191\231\130\185\239\188\140\229\188\128\229\167\139\228\184\128\233\128\154\231\191\187\230\137\190\121\121\121\060\038\112\077\121\060\038\112\077\121\060\038\112\077\121\060\038\112\077\230\137\190\229\136\176\228\186\134\239\188\129\232\191\153\229\176\177\230\152\175\231\187\136\231\171\175\239\188\129\060\038\112\077"), 
		Buttons = {
			_AR0fF("\230\141\161\232\181\183")
		}, 
		Callback = function(action)
			if action ~= nil then
				_Urwigo.MessageBox{
					Text = _AR0fF("\227\128\144\230\150\176\231\137\169\229\147\129\232\142\183\229\190\151\239\188\154\230\151\160\231\189\145\231\187\156\231\154\132\231\187\136\231\171\175\227\128\145\060\038\112\077\228\189\160\230\139\191\232\181\183\231\187\136\231\171\175\239\188\140\230\137\147\229\188\128\230\153\131\228\186\134\228\184\164\228\184\139\060\038\112\077\226\128\157\230\151\160\231\189\145\231\187\156\232\191\158\230\142\165\226\128\156\060\038\112\077\229\157\143\228\186\134\239\188\140\231\187\136\231\171\175\229\175\185\233\155\182\228\187\182\231\154\132\229\174\154\228\189\141\229\159\186\228\186\142\229\159\186\231\171\153\231\189\145\231\187\156\239\188\140\231\142\176\229\156\168\229\159\186\231\171\153\230\151\169\229\176\177\229\129\156\232\191\144\228\186\134"), 
					Buttons = {
						_AR0fF("\233\130\163\230\128\142\228\185\136\229\138\158\239\188\159")
					}, 
					Callback = function(action)
						if action ~= nil then
							_Urwigo.MessageBox{
								Text = _AR0fF("\228\189\160\228\187\148\231\187\134\229\155\158\230\131\179\239\188\140\233\128\154\229\184\184\229\174\154\228\189\141\233\156\128\232\166\129\228\184\137\228\184\170\229\159\186\231\171\153\239\188\140\229\141\179\229\136\187\229\141\179\229\143\175\232\191\148\229\155\158\233\155\182\228\187\182\231\154\132\228\189\141\231\189\174\121\121\121\228\189\134\230\152\175\230\156\128\228\189\142\228\184\128\228\184\170\229\159\186\231\171\153\228\185\159\232\131\189\231\148\168\239\188\140\229\143\170\233\156\128\232\166\129\229\141\149\228\184\170\229\159\186\231\171\153\229\176\177\229\143\175\228\187\165\229\174\154\228\189\141\231\187\136\231\171\175\228\184\142\233\155\182\228\187\182\231\154\132\232\183\157\231\166\187\060\038\112\077\232\128\140\228\189\160\230\173\163\229\165\189\232\174\176\229\190\151\230\156\137\228\184\128\230\149\180\228\184\170\229\164\135\231\148\168\229\159\186\231\171\153\229\156\168\229\147\170\239\188\129"), 
								Buttons = {
									_AR0fF("\229\156\168\229\147\170\239\188\159")
								}, 
								Callback = function(action)
									if action ~= nil then
										_Urwigo.MessageBox{
											Text = _AR0fF("\229\164\135\231\148\168\229\159\186\231\171\153\228\184\186\228\186\134\229\143\175\228\187\165\232\166\134\231\155\150\229\176\189\229\143\175\232\131\189\229\164\154\231\154\132\229\140\186\229\159\159\239\188\140\228\189\141\228\186\142\230\149\180\228\184\170\229\140\186\229\159\159\231\154\132\230\156\128\233\171\152\229\164\132\060\038\112\077\232\191\153\231\137\135\229\140\186\229\159\159\231\154\132\230\156\128\233\171\152\229\164\132\121\121\121\232\128\129\229\177\177\231\158\173\230\156\155\229\143\176\239\188\129\060\038\112\077\227\128\144\230\150\176\228\187\187\229\138\161\230\183\187\229\138\160\239\188\154\229\137\141\229\190\128\232\128\129\229\177\177\231\158\173\230\156\155\229\143\176\229\144\175\229\138\168\229\164\135\231\148\168\229\159\186\231\171\153\227\128\145"), 
											Buttons = {
												_AR0fF("\232\181\176\239\188\129")
											}
										}
									end
								end
							}
						end
					end
				}
			end
		end
	}
	_E7Yob:MoveTo(Player)
	_lLQrR.Active = false
	_KQwil.Active = true
	_sF4a.Complete = true
	_46MF.Active = true
end
function _KQwil:OnEnter()
	_EBu0a = _AR0fF("\050\016\093\039\089\108")
	_Urwigo.MessageBox{
		Text = _AR0fF("\231\187\143\232\191\135\232\183\139\230\182\137\239\188\140\228\189\160\231\187\136\228\186\142\230\137\190\229\136\176\228\186\134\229\159\186\231\171\153\230\137\128\229\156\168\239\188\129"), 
		Buttons = {
			_AR0fF("\229\165\189\230\172\184")
		}, 
		Callback = function(action)
			if action ~= nil then
				_Urwigo.MessageBox{
					Text = _AR0fF("\229\143\175\230\152\175\239\188\140\229\164\135\231\148\168\229\159\186\231\171\153\230\178\161\230\156\137\231\148\181\230\186\144\232\191\158\230\142\165\239\188\140\230\151\160\230\179\149\229\183\165\228\189\156\239\188\129"), 
					Buttons = {
						_AR0fF("\229\149\138\239\188\159")
					}, 
					Callback = function(action)
						if action ~= nil then
							_Urwigo.MessageBox{
								Text = _AR0fF("\229\146\179\229\146\179\239\188\140\233\128\151\228\189\160\231\154\132\239\188\140\230\178\161\230\156\137\231\172\172\228\184\137\233\152\182\230\174\181\228\186\134\060\038\112\077\228\189\160\230\136\144\229\138\159\229\144\175\229\138\168\228\186\134\229\164\135\231\148\168\229\159\186\231\171\153\239\188\140\229\164\169\231\186\191\229\188\128\229\167\139\230\151\139\232\189\172\121\121\121\060\038\112\077"), 
								Callback = function(action)
									if action ~= nil then
										_Urwigo.MessageBox{
											Text = _AR0fF("\056\231\187\136\231\171\175\228\184\138\231\186\191\230\136\144\229\138\159\239\188\140\229\189\147\229\137\141\229\159\186\231\171\153\239\188\154\013\226\128\157\060\038\112\077\230\136\144\229\138\159\228\186\134\239\188\129\231\187\136\228\186\142\060\038\112\077\227\128\144\230\150\176\228\187\187\229\138\161\239\188\154\230\137\190\229\136\176\233\155\182\228\187\182\227\128\145")
										}
									end
								end
							}
						end
					end
				}
			end
		end
	}
	_fa8.Active = true
	_KQwil.Active = false
	_E7Yob:MoveTo(nil)
	_Jvuml:MoveTo(Player)
	_46MF.Complete = true
	_mXW.Active = true
end
function _fa8:OnEnter()
	_EBu0a = _AR0fF("\050\084\061\036")
	_Urwigo.MessageBox{
		Text = _AR0fF("\229\164\169\229\147\170\107\230\178\161\230\131\179\229\136\176\228\189\160\231\156\159\231\154\132\229\129\154\229\136\176\228\186\134\239\188\129"), 
		Callback = function(action)
			if action ~= nil then
				_Urwigo.MessageBox{
					Text = _AR0fF("\228\189\160\232\191\152\232\174\176\229\190\151\233\155\182\228\187\182\232\151\143\229\156\168\228\186\134\228\184\128\228\184\170\229\134\153\231\157\128\060\038\112\077\226\128\156\060\038\112\077\226\134\144\230\163\174\230\158\151\229\173\166\229\160\130\107\063\116\003\046\005\065\229\141\151\229\133\165\229\143\163\226\134\146\060\038\112\077\226\134\144\230\157\190\230\158\156\230\172\162\228\185\144\229\155\173\107\229\141\171\231\148\159\233\151\180\226\134\145\060\038\112\077\226\134\144\231\171\165\231\170\157\232\182\163\060\038\112\077\226\128\157\060\038\112\077\231\154\132\232\183\175\231\137\140\230\151\129\060\038\112\077\233\130\163\233\135\140\229\186\148\232\175\165\230\156\137\230\149\176\229\157\151\231\159\179\229\164\180\239\188\140\229\174\131\229\176\177\230\152\175\228\184\128\229\157\151\229\129\135\231\159\179\229\164\180\239\188\140\232\162\171\231\162\142\231\159\179\229\141\138\230\142\169\229\156\168\229\164\167\231\159\179\229\164\180\228\185\139\229\144\142\060\038\112\077\230\137\190\229\136\176\229\174\131\239\188\140\231\173\190\228\184\138\228\189\160\231\154\132\229\164\167\229\144\141\239\188\140\228\186\164\230\141\162\014\096\109\021\109\089\116\239\188\140\108\109\014\107\084\089\116\111\239\188\140\228\186\171\229\143\151\232\142\183\232\131\156\232\128\133\229\186\148\229\190\151\231\154\132\232\141\163\232\170\137\229\144\167\239\188\129")
				}
			end
		end
	}
	_Jvuml:MoveTo(nil)
	_MDT3h:MoveTo(Player)
	_fa8.Visible = true
	_mXW.Complete = true
end
function _E7Yob:On_Nm1x(target)
	_Urwigo.MessageBox{
		Text = _AR0fF("\230\151\160\231\189\145\231\187\156\232\191\158\230\142\165")
	}
end
function _Jvuml:On_5e3(target)
	_Urwigo.OldDialog{
		{
			Text = _AR0fF("\231\148\181\233\135\143\239\188\154\013\018\018\115\107\063\116\003\046\005\065\229\159\186\231\171\153\239\188\154\239\188\136\013\023\101\239\188\137\073\073\115\060\038\112\077\230\173\163\229\156\168\229\174\154\228\189\141\121\121\121\060\038\112\077\229\189\147\229\137\141\228\189\141\231\189\174\232\183\157\231\166\187\233\155\182\228\187\182\239\188\154")
		}, 
		{
			Text = tostring(Wherigo.VectorToPoint(Player.ObjectLocation, _fa8.OriginalPoint):GetValue "m")
		}, 
		{
			Text = _AR0fF("\231\177\179")
		}
	}
end

-- Urwigo functions --

-- Begin user functions --
-- End user functions --
return _ZgAaB

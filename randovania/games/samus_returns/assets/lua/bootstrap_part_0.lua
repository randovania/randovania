Game.DoFile('actors/items/randomizerpowerup/scripts/randomizerpowerup.lua')
RL.Pickups = {}
function RL.GetCollectedIndicesAndSend()
    if Game.GetCurrentGameModeID()  ~= "INGAME" then return "not-in-game" end
    local r,v,i,p = {},0,1,Game.GetPlayerBlackboardSectionName()
    for _,t in ipairs(RL.Pickups) do
        if Blackboard.GetProp(p,t) then v=v+i end
        i=i*2;if i>=256 then table.insert(r,string.char(v));v=0;i=1 end
    end
    if i>1 then table.insert(r,string.char(v)) end
    RL.SendIndices("locations:"..table.concat(r))
end
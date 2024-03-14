function RL.InventoryIndex()
    local playerSection =  Game.GetPlayerBlackboardSectionName()
    return Blackboard.GetProp(playerSection, "InventoryIndex") or 0
end

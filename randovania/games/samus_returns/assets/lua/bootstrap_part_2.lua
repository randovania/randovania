function RL.InventoryIndex()
    local playerSection =  Game.GetPlayerBlackboardSectionName()
    return Blackboard.GetProp(playerSection, "InventoryIndex") or 0
end
function RL.ReceivedPickups()
    local playerSection =  Game.GetPlayerBlackboardSectionName()
    return Blackboard.GetProp(playerSection, "ReceivedPickups") or 0
end
function RL.GetReceivedPickupsAndSend(reset)
    if reset then
        RL.PendingPickup = nil
    end
    RL.SendReceivedPickups(tostring(RL.ReceivedPickups()))
end
function RL.GivePendingPickup()
    if Scenario.IsUserInteractionEnabled(true) and not Game.IsCutscenePlaying() then
        Scenario.QueueAsyncPopup(RL.PendingPickup.msg, 7.0)
        Game.AddSF(7.5, "RL.GetReceivedPickupsAndSend", "b", true)
        RL.ConfirmPickup()
    else
        Game.AddSF(0.5, "RL.GivePendingPickup", "")
    end
end
function RL.ConfirmPickup()
    RL.PendingPickup.code()
    local playerSection = Game.GetPlayerBlackboardSectionName()
    Blackboard.SetProp(playerSection, "ReceivedPickups", "f", RL.ReceivedPickups()+1)
end
function RL.ReceivePickup(msg,lua_code,receivedPickupIndex,inventoryIndex)
    if not RL.PendingPickup then
        if receivedPickupIndex == RL.ReceivedPickups() and inventoryIndex == RL.InventoryIndex() then
            RL.PendingPickup={msg=msg, code=assert(loadstring(lua_code))}
            Game.AddSF(0, "RL.GivePendingPickup", "")
        else
            Game.AddSF(0, "RL.GetInventoryAndSend", "")
            Game.AddSF(0.05, "RL.GetReceivedPickupsAndSend", "b", false)
        end
    end
end
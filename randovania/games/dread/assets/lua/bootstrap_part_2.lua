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
    if Scenario.IsUserInteractionEnabled(true) then
        Scenario.QueueAsyncPopup(RL.PendingPickup.msg, 7.0)
        Game.AddSF(7.5, "RL.GetReceivedPickupsAndSend", "b", true)
        RL.ConfirmPickup()
    else
        Game.AddSF(0.5, "RL.GivePendingPickup", "")
    end
end
function RL.ConfirmPickup()
    RL.PendingPickup.cls.OnPickedUp(nil,RL.PendingPickup.progression)
    Scenario.WriteToPlayerBlackboard("ReceivedPickups","f",RL.ReceivedPickups()+1)
end
function RL.ReceivePickup(msg,cls,progression_string,receivedPickupIndex,inventoryIndex)
    if not RL.PendingPickup then
        if receivedPickupIndex == RL.ReceivedPickups() and inventoryIndex == RL.InventoryIndex() then
            progression = assert(loadstring("return " .. progression_string))()
            RL.PendingPickup={cls=cls,progression=progression,msg=msg}
            Game.AddSF(0, "RL.GivePendingPickup", "")
        else
            Game.AddSF(0, "RL.GetInventoryAndSend", "")
            Game.AddSF(0.05, "RL.GetReceivedPickupsAndSend", "b", false)
        end
    end
end
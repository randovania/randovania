function RL.UpdateRDVClient(new_scenario)
    -- TODO:...
    -- RL.GetGameStateAndSend()
    if Game.GetCurrentGameModeID() == 'INGAME' then
        local playerSection =  Game.GetPlayerBlackboardSectionName()
        local currentSaveRandoIdentifier = Blackboard.GetProp(playerSection, "THIS_RANDO_IDENTIFIER")
        if currentSaveRandoIdentifier ~= Init.sThisRandoIdentifier then
            return
        end
        if new_scenario == true then
            RL.PendingPickup = nil
        end
        Game.AddSF(0, "RL.GetInventoryAndSend", "")
        Game.AddSF(0.05, "RL.GetCollectedIndicesAndSend", "")
        -- TODO:...
        -- if RL.PendingPickup == nil then
        --     Game.AddSF(0.05, "RL.GetReceivedPickupsAndSend", "b", false)
        -- end
    end
end

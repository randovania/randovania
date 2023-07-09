function RL.GetGameStateAndSend()
    local current_state = Game.GetCurrentGameModeID()
    if current_state == 'INGAME' then
        RL.SendNewGameState(Game.GetScenarioID())
    else
        RL.SendNewGameState(current_state)
    end
end

function RL.UpdateRDVClient(new_scenario)
    RL.GetGameStateAndSend()
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
        if RL.PendingPickup == nil then
            Game.AddSF(0.05, "RL.GetReceivedPickupsAndSend", "b", false)
        end
    end
end

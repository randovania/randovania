function RL.GetInventoryAndSend()
    local r={}
    local playerName = Game.GetPlayerName()
    for i,n in ipairs(RL.InventoryItems) do
        r[i]=Game.GetItemAmount(playerName, n)
    end
    local inventory = string.format("[%s]",table.concat(r,","))
    local currentIndex = string.format('"index": %s', RL.InventoryIndex())
    RL.SendInventory(string.format('{%s,"inventory":%s}', currentIndex, inventory))
end
RL.InventoryItems=TEMPLATE("inventory")
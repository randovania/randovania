function RL.GetInventoryAndSend()
    local r={}
    for i,n in ipairs(RL.InventoryItems) do
        r[i]=RandomizerPowerup.GetItemAmount(n)
    end
    local inventory = string.format("[%s]",table.concat(r,","))
    local currentIndex = string.format('"index": %s', RL.InventoryIndex())
    RL.SendInventory(string.format('{%s,"inventory":%s}', currentIndex, inventory))
end
RL.InventoryItems=TEMPLATE("inventory")
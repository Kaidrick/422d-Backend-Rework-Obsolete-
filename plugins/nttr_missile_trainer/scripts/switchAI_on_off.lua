local function AIOff(groupName)
    Group.getByName(groupName):getController():setOnOff(false)
end
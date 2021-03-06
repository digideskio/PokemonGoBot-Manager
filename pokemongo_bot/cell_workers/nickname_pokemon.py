from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.cell_workers.base_task import BaseTask

class NicknamePokemon(BaseTask):
    def initialize(self):
        self.template = self.config.get('nickname_template','').lower().strip()
        if self.template == "{name}":
            self.template = ""
    
    def work(self):
        try:
            inventory = reduce(dict.__getitem__, ["responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], self.bot.get_inventory())
        except KeyError:
            pass
        else:
            pokemon_data = self._get_inventory_pokemon(inventory)
            for pokemon in pokemon_data:
                self._nickname_pokemon(pokemon) 
            
    def _get_inventory_pokemon(self,inventory_dict):
        pokemon_data = []
        for inv_data in inventory_dict:
            try:
                pokemon = reduce(dict.__getitem__,['inventory_item_data','pokemon_data'],inv_data)
            except KeyError:
                pass
            else:
                if not pokemon.get('is_egg',False):
                    pokemon_data.append(pokemon)
        return pokemon_data
        
    def _nickname_pokemon(self,pokemon):
        """This requies a pokemon object containing all the standard fields: id, ivs, cp, etc"""
        new_name = ""
        instance_id = pokemon.get('id',0)
        if not instance_id:
            logger.log("Pokemon instance id returned 0. Can't rename.",'red')
            return
        id = pokemon.get('pokemon_id',0)-1
        name = self.bot.pokemon_list[id]['Name']
        cp = pokemon.get('cp',0)
        iv_attack = pokemon.get('individual_attack',0)
        iv_defense = pokemon.get('individual_defense',0)
        iv_stamina = pokemon.get('individual_stamina',0)
        iv_list = [iv_attack,iv_defense,iv_stamina]
        iv_ads = "/".join(map(str,iv_list))
        iv_sum = sum(iv_list)
        iv_pct = "{:0.0f}".format(100*iv_sum/45.0)
        log_color = 'red'
        try:
            new_name = self.template.format(name=name,
                                    id=id,
                                    cp=cp,
                                    iv_attack=iv_attack,
                                    iv_defense=iv_defense,
                                    iv_stamina=iv_stamina,
                                    iv_ads=iv_ads,
                                    iv_sum=iv_sum,
                                    iv_pct=iv_pct)[:12]
        except KeyError as bad_key:
            logger.log("Unable to nickname {} due to bad template ({})".format(name,bad_key),log_color)
        if pokemon.get('nickname', "") == new_name:
            return
        self.bot.api.nickname_pokemon(pokemon_id=instance_id,nickname=new_name)
        response = self.bot.api.call()
        sleep(1.2)
        try: 
            result =  reduce(dict.__getitem__, ["responses", "NICKNAME_POKEMON"], response)
        except KeyError:
            logger.log("Attempt to nickname received bad response from server.",log_color)
            if self.bot.config.debug:
                logger.log(response,log_color)
            return
        result = result['result']
        if new_name == "":
            new_name = name
        output = {
            0: 'Nickname unset',
            1: 'Nickname set successfully! {} is now {}'.format(name,new_name),
            2: 'Invalid nickname! ({})'.format(new_name),
            3: 'Pokemon not found.',
            4: 'Pokemon is egg'
        }[result]
        if result==1:
            log_color='green'
            pokemon['nickname'] = new_name
        logger.log(output,log_color)
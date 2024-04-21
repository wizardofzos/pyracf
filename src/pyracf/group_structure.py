import warnings

class GroupStructureTree(dict):
    ''' Dict with group names starting from SYS1 (group tree) or from (multiple) user IDs (owner tree).
    Printing these objects, the tree will be formatted as Unix tree (default, or after .setformat('unix') or with mainframe characters (after .setformat('simple').
    The dict may be accessed with .tree '''

    def __init__(self,df,linkup_field="GPBD_SUPGRP_ID"):
        # get all owners... (group or user) or all superior groups
        tree = {}
        where_is = {}
        higher_ups = df.groupby(linkup_field)
        for higher_up in higher_ups.groups.keys():
            if higher_up not in tree:
                tree[higher_up] = []
                for group in higher_ups.get_group(higher_up)['GPBD_NAME'].values:
                    tree[higher_up].append(group)
                    where_is[group] = tree[higher_up]
        # initially, for an owner tree, anchor can be a user (like IBMUSER) or a group
        # now we gotta condense it, so only IBMUSER and other group owning users are at top level
        # for group tree, we should end up with SYS1, and a list of groups
        deletes = []
        for anchor in tree:
            if anchor in where_is:
                supgrpMembers = where_is[anchor]
                ix = supgrpMembers.index(anchor)
                supgrpMembers[ix] = {anchor: tree[anchor]}
                deletes.append(anchor)
        for anchor in deletes:
            tree.pop(anchor)
        if '' in tree:  # bring SYS1 to the top, supgroup of SYS1 is ''
            tree = tree[''][0]
        super().__init__(tree)
        self._format = 'unix'

    def __str__(self):
        ''' what happens when print(object) is issued '''
        return self.simple_format(self) if self._format=='simple' else self.unix_format(self)
        
    def format(self,format='unix'):
        ''' return printable tree '''
        if format in ['unix','simple']:
            return self.simple_format(self) if format=='simple' else self.unix_format(self)
        else:
            warnings.warn(f'Unsupported format value {format}, select unix or simple.')

    def setformat(self,format='unix'):
        ''' set default format for next print '''
        if format in ['unix','simple']:
            self._format = format
        else:
            warnings.warn(f'Unsupported format value {format}, select unix or simple.')

    def unix_format(self,branch=None,prefix=''):
        ''' print groups, prefixed with vertical bars to show depth '''
        BOX_START = u'\u250C'
        BOX_ENTRY = u'\u251C'
        BOX_CONT = u'\u2502'
        BOX_END = u'\u2514'
        if not branch:
            branch = self.tree
        info = ''
        if type(branch)==str:
            info += prefix + ' ' +  str(branch) + '\n'
        elif type(branch)==list:
            # indent 1 level, prev level continues with just a bar
            if prefix and prefix[-1]==BOX_ENTRY:
                prefix = prefix[0:-1]+BOX_CONT
            for node in branch:
                # last node in a branch gets an END indicator, others get a T
                mark = ' '+BOX_END if (node==branch[-1]) else ' '+BOX_ENTRY
                info += self.unix_format(node,prefix=prefix+mark)
        else:
            for (node,values) in branch.items():
                info += prefix + ' ' + str(node) + '\n'
                # only 1 END indicator (which we just printed)
                if prefix and prefix[-1]==BOX_END:
                    prefix = prefix[0:-1]+' '
                info += self.unix_format(values,prefix=prefix)
        return info

    def simple_format(self,branch=None,depth=0):
        ''' print groups, prefixed with vertical bars to show depth '''
        if not branch:
            branch = self.tree
        info = ''
        if type(branch)==str:
            info += ' |'*depth + ' ' +  str(branch) + '\n'
        elif type(branch)==list:
            depth += 1
            for node in branch:            
                info += self.simple_format(node,depth)
        else:
            for (node,values) in branch.items():
                info += ' |'*depth + ' '  + str(node) + '\n'
                info += self.simple_format(values,depth)
        return info

    @property
    def tree(self):
        warnings.warn('.tree attribute is deprecated, this is now the default return value of the tree objected')
        return self


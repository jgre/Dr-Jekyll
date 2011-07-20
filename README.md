# Dr Jekyll

Dr Jekyll is a command-line tool for editing a blog based on
[Jekyll](http://jekyllrb.com/). It gives you commands for creating and editing
posts, managing drafts including a preview function, and gives you a better
overview of you writing.

## Installation

Dr Jekyll depends on Jekyll which is written in Ruby so you need a ruby
interpreter and RubyGems installed. Install Jekyll using RubyGems:

    gem install jekyll

(See [Jekyll's Install page](https://github.com/mojombo/jekyll/wiki/install) if
you hava any problems here)

Dr Jekyll is written in Python and requires at least version 2.7 to be
installed.

**TODO: describe installation**

## Usage

Dr Jekyll provides the `drjekyll` command with a number of subcommands for
different tasks.

### Directory Structure

Dr Jekyll slightly changes the original [Jekyll
structure](https://github.com/mojombo/jekyll/wiki/Usage) to accomotate drafts.

There are two new directories: `_drafts` and `_published`. The `_posts`
directory is not used for the articles you edit but Dr Jekyll puts everything
you want to preview there. `_drafts` and `_published`
are like the original `_posts` directory but drafts and published posts are
separate.

### Subcommands

All commands share some arguments:

    --config CONFIG       Set the path to the configuration file (default:
                          ~/.drjekyll)
    --base-dir PATH       Set the path to your blog (default: .)

### Creating a New Draft

    drjekyll.py new [-h] [--editor EDITOR] [--date DATE]
                    [--extension EXTENSION]
                    title

The `new` command creates a new file in the drafts directory. The file name is
today's date followed by the title in lower cased, the words connected by
dashes. 

    --editor EDITOR    Set the command to launch an editor for the post
    --date DATE        Set date and time for the new post (default: now). The
                       format is "YEAR-MONTH-DAY HOUR:MINUTE".
    --extension EXT    Set the file extension (default: .md)

### Publishing a Draft

    drjekyll publish TITLE
    drjekyll.py publish [-h] [--date DATE] [title ...]

The title can also be a regular expression that is matched againts all titles.
If the match is ambiguous, you will be asked to select the post from a list.

If no title is given, the most recent post or draft is published.

The source file for the post is moved from `_drafts` to `_posts` and the date
in the file name is updated to today's date. In the file the YAML-frontmatter
is updated with the the current date and time.

    --date DATE  Set date and time for the post (default: now). The format is
                 "YEAR-MONTH-DAY HOUR:MINUTE".

### Listing Your Posts

    drjekyll.py ls [-h] [--published | --drafts]

The `ls` command gives you an overview of your posts. Draft post are listed in
green.

    --published  Show only published posts
    --drafts     Show only drafts

### Editing a Post

    drjekyll.py edit [-h] [--editor EDITOR] [title ...]

The title can also be a regular expression that is matched againts all titles.
If the match is ambiguous, you will be asked to select the post from a list.

If no title is given, the most recent post or draft is edited.

    --editor EDITOR  Set the command to launch an editor for the post

### Gererating the Site

    drjekyll.py generate [-h] [--published] [--auto]

With the `generate` command you tell Dr Jekyll to put all posts into the
`_posts` directory so that you can run the original Jekyll to render the site.

    --published  Only generate the published posts
    --auto       Wait for changes and automatically regenerate
 
### Deleting a Post

    drjekyll.py rm [-h] [title ...]

The title can also be a regular expression that is matched againts all titles.
If the match is ambiguous, you will be asked to select the post from a list.

## Configuration

Some options can be set in a config file located in your home directory named
`.drjekyll`.

The file must start with a section header for the `DEFAULT` section. Options
have the form `KEY: VALUE`. Valid options are:

    editor      Set the command to launch an editor for the post
    base-dir    Set the path to your blog
    extension   Set the file extension
